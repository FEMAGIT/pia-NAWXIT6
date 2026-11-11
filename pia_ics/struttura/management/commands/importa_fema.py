"""Importa nella piattaforma i dati di produzione dal DB SQL Server PIA_FEMA.

Il DB PIA_FEMA (unico database, tre schemi) sostituisce i vecchi database separati:
    PIA_FemaWms.dbo.*        -> PIA_FEMA.wms.*     (magazzino blocchi)
    PIA_FEMA_PRODPLAN.dbo.*  -> PIA_FEMA.NEXUM.*   (commesse)
    PIA_FEMA.dbo.*           -> PIA_FEMA.dbo.*     (ordini, lavorazioni, log macchina)

Catena di tracciabilità usata (vedi "31_Diagramma ER del DB e architettura SW di produzione"):
    wms.ARTICOLI.Id <- dbo.ORDINI_BLOCCO.IdBlocco / IdOrdine -> dbo.Ordini.ID_Ordine
    dbo.Ordini.Note "id:xxx" -> NEXUM.V_COMMESSE_ESPLOSE.idRecord (= NEXUM.COMMESSA.ID_RIGA_ORDINE)
    in mancanza della nota: Ordini.ID_Ordine -> NEXUM.COMMESSA_ORDINI.CODICE_COMMESSA -> NEXUM.COMMESSA

L'import è idempotente: può essere rilanciato per aggiornare i dati. I log macchina
vengono importati in modo incrementale (solo gli ID successivi all'ultimo importato).

Connessione: variabili d'ambiente FEMA_DB_HOST, FEMA_DB_PORT, FEMA_DB_NAME, FEMA_DB_USER,
FEMA_DB_PASSWORD (sovrascrivibili con le opzioni da riga di comando).
"""

import os
from collections import defaultdict
from datetime import date
from zoneinfo import ZoneInfo

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from autenticazione.models import Cliente
from struttura.fema import TIPI_ATTIVITA, formatta_misura, id_record_da_note, interpreta_log
from struttura.models import (Articolo, Attività, Commessa, Lavorazione, Log, Macchina, Ordine,
                              OrdiniBlocco, TipoMacchina)


class Command(BaseCommand):
    help = "Importa ordini, commesse, blocchi, lavorazioni e log macchina dal DB SQL Server PIA_FEMA."

    def add_arguments(self, parser):
        parser.add_argument("--host", default=os.getenv("FEMA_DB_HOST", "127.0.0.1"))
        parser.add_argument("--port", type=int, default=int(os.getenv("FEMA_DB_PORT", "1433")))
        parser.add_argument("--database", default=os.getenv("FEMA_DB_NAME", "PIA_FEMA"))
        parser.add_argument("--user", default=os.getenv("FEMA_DB_USER", ""))
        parser.add_argument("--password", default=os.getenv("FEMA_DB_PASSWORD", ""))
        parser.add_argument(
            "--fuso-orario", default=os.getenv("FEMA_DB_TIMEZONE", "Europe/Rome"),
            help="Fuso orario delle date salvate (senza fuso) nel DB di produzione.",
        )
        parser.add_argument(
            "--cliente-id", type=int,
            help="Cliente a cui associare le macchine nuove (obbligatorio se i clienti sono più di uno).",
        )
        parser.add_argument(
            "--log-completo", action="store_true",
            help="Rilegge tutti i log macchina invece dei soli nuovi (quelli già presenti vengono saltati).",
        )

    def handle(self, *args, **opts):
        self.fuso = ZoneInfo(opts["fuso_orario"])
        self.cliente_id = opts["cliente_id"]
        conn = self._connetti(opts)
        try:
            cur = conn.cursor(as_dict=True)
            with transaction.atomic():
                macchine = self._importa_macchine(cur)
                articoli = self._importa_articoli(cur)
                ordini, righe_ordine = self._importa_ordini(cur)
                self._importa_ordini_blocco(cur, ordini, articoli)
                commesse_riga = self._importa_commesse(cur, ordini, righe_ordine)
                self._importa_lavorazioni(cur, macchine, commesse_riga)
                self._importa_log(cur, macchine, opts["log_completo"])
        finally:
            conn.close()
        self.stdout.write(self.style.SUCCESS("Import da PIA_FEMA completato."))

    # ------------------------------------------------------------------ utilità

    def _connetti(self, opts):
        try:
            import pymssql
        except ImportError as exc:
            raise CommandError("Modulo pymssql mancante: eseguire 'pip install pymssql'.") from exc
        try:
            return pymssql.connect(
                server=opts["host"], port=opts["port"], user=opts["user"],
                password=opts["password"], database=opts["database"], charset="UTF-8",
            )
        except pymssql.Error as exc:
            raise CommandError(f"Connessione a {opts['host']}:{opts['port']}/{opts['database']} fallita: {exc}") from exc

    def _aware(self, valore):
        if valore is None or timezone.is_aware(valore):
            return valore
        return timezone.make_aware(valore, self.fuso)

    @staticmethod
    def _testo(valore):
        return (valore or "").strip()

    def _report(self, nome, creati, aggiornati=0, extra=""):
        self.stdout.write(f"  {nome}: {creati} nuovi, {aggiornati} aggiornati{extra}")

    # ---------------------------------------------------------------- anagrafiche

    def _cliente_per_nuove_macchine(self):
        if self.cliente_id:
            try:
                return Cliente.objects.get(pk=self.cliente_id)
            except Cliente.DoesNotExist as exc:
                raise CommandError(f"Cliente con id {self.cliente_id} inesistente.") from exc
        clienti = list(Cliente.objects.all()[:2])
        if len(clienti) == 1:
            return clienti[0]
        raise CommandError(
            "Per creare le macchine importate serve un cliente: crearne uno dall'admin "
            "oppure indicarlo con --cliente-id."
        )

    def _importa_macchine(self, cur):
        cur.execute("""
            SELECT m.IDENTIFICATIVO, m.DESCRIZIONE, t.DescBreve, t.Descrizione AS DescTipo
            FROM dbo.MACCHINA m
            LEFT JOIN dbo.TipoMacchina t ON t.TipoMacchina = m.TipoMacchina
        """)
        macchine, creati, aggiornati = {}, 0, 0
        for r in cur.fetchall():
            identificativo = str(r["IDENTIFICATIVO"])
            desc_breve = self._testo(r["DescBreve"])
            desc_tipo = self._testo(r["DescTipo"])[:50] or desc_breve

            tipo = (TipoMacchina.objects.filter(tipomacchina=desc_breve).first()
                    or TipoMacchina.objects.filter(desctipomacchina=desc_tipo).first())
            if tipo is None:
                tipo = TipoMacchina.objects.create(tipomacchina=desc_breve, desctipomacchina=desc_tipo)

            valori = {
                "tipo_macchina": tipo,
                "desctipomacchina": desc_tipo,
                "descrmacchina": self._testo(r["DESCRIZIONE"]) or desc_breve,
            }
            macchina = Macchina.objects.filter(identificativo=identificativo).first()
            if macchina:
                for campo, valore in valori.items():
                    setattr(macchina, campo, valore)
                macchina.save()
                aggiornati += 1
            else:
                macchina = Macchina.objects.create(
                    identificativo=identificativo, cliente=self._cliente_per_nuove_macchine(), **valori
                )
                creati += 1
            macchine[identificativo] = macchina
        self._report("Macchine", creati, aggiornati)
        return macchine

    def _importa_articoli(self, cur):
        cur.execute("""
            SELECT Id, Tipo, Codice, Altezza, Larghezza, Spessore, Peso, DataCreazione
            FROM wms.ARTICOLI
        """)
        articoli, creati, aggiornati = {}, 0, 0
        for r in cur.fetchall():
            valori = {
                "tipo": self._testo(r["Tipo"]),
                "codice": self._testo(r["Codice"]),
                "altezza": r["Altezza"] or 0,
                "larghezza": r["Larghezza"] or 0,
                "spessore": r["Spessore"] or 0,
                "peso": r["Peso"] or 0,
                "data_creazione": self._aware(r["DataCreazione"]) or timezone.now(),
            }
            # Riusa un articolo importato in passato da CSV (senza id_esterno) con lo stesso codice
            articolo = (Articolo.objects.filter(id_esterno=r["Id"]).first()
                        or Articolo.objects.filter(id_esterno__isnull=True, codice=valori["codice"]).first())
            if articolo:
                for campo, valore in valori.items():
                    setattr(articolo, campo, valore)
                articolo.id_esterno = r["Id"]
                articolo.save()
                aggiornati += 1
            else:
                articolo = Articolo.objects.create(id_esterno=r["Id"], **valori)
                creati += 1
            articoli[r["Id"]] = articolo
        self._report("Articoli (blocchi)", creati, aggiornati)
        return articoli

    # -------------------------------------------------------------------- ordini

    def _importa_ordini(self, cur):
        cur.execute("""
            SELECT ID_Ordine, NumRiga, DescOrdine, Qta_DaFare, Qta_Fatte, Macchina,
                   DataConsegna, Materiale, Note, DataInizio, DataFine
            FROM dbo.Ordini
            ORDER BY ID_Ordine, NumRiga
        """)
        righe_ordine = defaultdict(list)
        for r in cur.fetchall():
            righe_ordine[self._testo(r["ID_Ordine"])].append(r)

        ordini, creati, aggiornati = {}, 0, 0
        for id_ordine, righe in righe_ordine.items():
            prima = righe[0]
            inizi = [r["DataInizio"] for r in righe if r["DataInizio"]]
            fini = [r["DataFine"] for r in righe if r["DataFine"]]
            ordine, nuovo = Ordine.objects.update_or_create(
                id_ordine_esterno=id_ordine,
                defaults={
                    "descordine": self._testo(prima["DescOrdine"]),
                    "dataconsegna": prima["DataConsegna"] or date.today(),
                    "materiale": self._testo(prima["Materiale"]),
                    "data_inizio": self._aware(min(inizi)) if inizi else None,
                    "data_fine": self._aware(max(fini)) if fini else None,
                },
            )
            ordini[id_ordine] = ordine
            creati += nuovo
            aggiornati += not nuovo
        self._report("Ordini", creati, aggiornati)
        return ordini, righe_ordine

    def _importa_ordini_blocco(self, cur, ordini, articoli):
        cur.execute("SELECT IdOrdine, IdBlocco FROM dbo.ORDINI_BLOCCO")
        creati, saltati = 0, 0
        for r in cur.fetchall():
            ordine = ordini.get(self._testo(r["IdOrdine"]))
            articolo = articoli.get(r["IdBlocco"])
            if not ordine or not articolo:
                saltati += 1
                continue
            _, nuovo = OrdiniBlocco.objects.get_or_create(ordine=ordine, articolo=articolo)
            creati += nuovo
        self._report("Blocchi per ordine", creati, extra=f", {saltati} senza ordine/blocco corrispondente")

    # ------------------------------------------------------------------ commesse

    def _importa_commesse(self, cur, ordini, righe_ordine):
        cur.execute("""
            SELECT idRecord, DES_MODELLI, COMPONENTE, DES_COMPON, PRIMIS, SECMIS, TERMIS,
                   DIMA, DES_CLIENTE, QTA, qta_lavorata
            FROM NEXUM.V_COMMESSE_ESPLOSE
        """)
        esplose = {r["idRecord"]: r for r in cur.fetchall()}

        cur.execute("SELECT ID_RIGA_ORDINE, ID_MACCHINA, CODICE_COMMESSA, DESCRIZIONE FROM NEXUM.COMMESSA")
        commesse_nexum = {r["ID_RIGA_ORDINE"]: r for r in cur.fetchall()}

        cur.execute("SELECT ID_Ordine, CODICE_COMMESSA FROM NEXUM.COMMESSA_ORDINI")
        ordini_per_codice = defaultdict(list)
        for r in cur.fetchall():
            ordini_per_codice[self._testo(r["CODICE_COMMESSA"])].append(self._testo(r["ID_Ordine"]))

        commesse_riga = {}  # (ID_Ordine, NumRiga) -> Commessa, usato per le lavorazioni
        id_record_collegati = set()
        creati = aggiornati = 0

        def salva(ordine, id_record, qta, qta_fatte, macchina_ordine):
            nonlocal creati, aggiornati
            v = esplose.get(id_record, {})
            c = commesse_nexum.get(id_record, {})
            primis, secmis = v.get("PRIMIS"), v.get("SECMIS")
            # Dima in mm "lunghezza X larghezza" del pezzo: la tracciabilità la confronta con
            # la corsa del Carro (asse Y), espressa in mm. DIMA di NEXUM è usata solo in mancanza.
            if primis is not None and secmis is not None:
                dima = f"{formatta_misura(primis)}X{formatta_misura(secmis)}"
            else:
                dima = self._testo(v.get("DIMA")) or None
            componente = self._testo(v.get("COMPONENTE")) or self._testo(v.get("DES_COMPON"))
            commessa, nuovo = Commessa.objects.update_or_create(
                ordine=ordine,
                id_record=str(id_record),
                defaults={
                    "id_macchina": self._testo(c.get("ID_MACCHINA")) or str(macchina_ordine or ""),
                    "codicecommessa": self._testo(c.get("CODICE_COMMESSA")) or ordine.descordine,
                    "descrizione": self._testo(c.get("DESCRIZIONE")),
                    "cliente": self._testo(v.get("DES_CLIENTE")),
                    "modello": self._testo(v.get("DES_MODELLI")) or None,
                    "componente": componente or None,
                    "desccomponente": self._testo(v.get("DES_COMPON")) or None,
                    "dima": dima,
                    # Spessore della fetta: confrontato con il passo della Sponda (asse X)
                    "profondità": v.get("TERMIS"),
                    "qta": qta,
                    "qtalav": qta_fatte or 0,
                },
            )
            creati += nuovo
            aggiornati += not nuovo
            return commessa

        # 1) Collegamento diretto riga ordine -> sagoma tramite la nota "id:xxx"
        for id_ordine, righe in righe_ordine.items():
            for r in righe:
                id_record = id_record_da_note(r["Note"])
                if id_record is None:
                    continue
                id_record_collegati.add(id_record)
                commesse_riga[(id_ordine, r["NumRiga"])] = salva(
                    ordini[id_ordine], id_record, r["Qta_DaFare"], r["Qta_Fatte"], r["Macchina"]
                )

        # 2) Sagome senza nota: Ordini -> COMMESSA_ORDINI -> COMMESSA -> V_COMMESSE_ESPLOSE
        for id_record, c in commesse_nexum.items():
            if id_record in id_record_collegati:
                continue
            v = esplose.get(id_record, {})
            for id_ordine in ordini_per_codice.get(self._testo(c["CODICE_COMMESSA"]), []):
                if id_ordine in ordini:
                    salva(ordini[id_ordine], id_record, v.get("QTA"), v.get("qta_lavorata"), None)

        self._report("Commesse (righe ordine)", creati, aggiornati)
        return commesse_riga

    def _importa_lavorazioni(self, cur, macchine, commesse_riga):
        cur.execute("""
            SELECT ID, ID_Ordine, NumRiga, Macchina, DataInizio, DataFine
            FROM dbo.LavorazioneOrdine
        """)
        creati, aggiornati, saltati = 0, 0, 0
        for r in cur.fetchall():
            commessa = commesse_riga.get((self._testo(r["ID_Ordine"]), r["NumRiga"]))
            macchina = macchine.get(str(r["Macchina"]))
            timestamp = self._aware(r["DataInizio"] or r["DataFine"])
            if not commessa or not macchina or not timestamp:
                saltati += 1
                continue
            _, nuovo = Lavorazione.objects.update_or_create(
                id_esterno=r["ID"],
                defaults={"commessa": commessa, "macchina": macchina, "timestamp": timestamp},
            )
            creati += nuovo
            aggiornati += not nuovo
        self._report("Lavorazioni", creati, aggiornati, extra=f", {saltati} saltate")

    # ----------------------------------------------------------------------- log

    def _importa_log(self, cur, macchine, completo):
        attivita = {tipo: Attività.objects.get_or_create(tipo_attività=tipo)[0] for tipo in TIPI_ATTIVITA}

        ultimo_id = 0
        if not completo:
            ultimo = Log.objects.filter(id_esterno__isnull=False).order_by("-id_esterno").first()
            ultimo_id = ultimo.id_esterno if ultimo else 0

        cur.execute(
            "SELECT ID, DataLogs, Descrizione, Macchina FROM dbo.Logs WHERE ID > %s ORDER BY ID",
            (ultimo_id,),
        )
        nuovi, saltati = [], 0
        for r in cur.fetchall():
            macchina = macchine.get(str(r["Macchina"]))
            if macchina is None or r["DataLogs"] is None:
                saltati += 1
                continue
            descrizione = self._testo(r["Descrizione"])
            info = interpreta_log(descrizione)
            nuovi.append(Log(
                id_esterno=r["ID"],
                macchine=macchina,
                attività=attivita[info.tipo_attivita],
                timestamp=self._aware(r["DataLogs"]),
                descrizione=descrizione[:250],
                input=info.input,
                output=info.output,
                valore=info.valore,
                lunghezza=info.lunghezza,
                larghezza=info.larghezza,
                unita_misura=info.unita_misura,
            ))
        Log.objects.bulk_create(nuovi, batch_size=1000, ignore_conflicts=True)
        self.stdout.write(
            f"  Log macchina: {len(nuovi)} letti dall'ID {ultimo_id + 1} (già presenti saltati), "
            f"{saltati} senza macchina corrispondente"
        )
