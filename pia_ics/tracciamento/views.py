import re
from datetime import timedelta

from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render

from django.views.generic import View
from django.views.generic import TemplateView
from struttura.fema import MOV_ALPHA, MOV_X, MOV_Y, PREFISSO_START_CICLO, STATO_CICLO
from struttura.models import Ordine, Commessa, Macchina, Log, QualitàAngoloAutomatico, QualitàTaglio

# Create your views here.

class StoricoOrdini(LoginRequiredMixin, View):
    def get(self, request):
        ordini = Ordine.objects.all()
        return render(request, 'storico.html', {"ordini": ordini})

class ScanQRCodeView(LoginRequiredMixin,TemplateView):
    template_name = 'scan_qrcode.html'


def leggi_codice_qr(qr_data):
    """Accetta "IdRecord:123", "id:123" (formato delle note ordine) oppure "123"."""
    testo = (qr_data or "").strip()
    if ":" in testo:
        prefisso, valore = testo.split(":", 1)
        if prefisso.strip().lower() in ("idrecord", "id"):
            return valore.strip()
    return testo


def nome_cliente(cliente):
    """"501.00141 GLAMOUR SOFA' S" -> "GLAMOUR SOFA' S"; "Nettuno sofa" resta invariato."""
    parole = (cliente or "").split()
    if parole and any(carattere.isdigit() for carattere in parole[0]):
        parole = parole[1:]
    return " ".join(parole)


def log_ciclo_ordine(ordine, macchina):
    """(log di start, log del ciclo) dell'ultimo ciclo automatico eseguito per l'ordine.

    Il ciclo inizia con "Start Ciclo Automatico ID_Ordine <id> (<lunghezza> x <larghezza> mm)" e
    termina al primo messaggio di ciclo successivo ("... Terminato" oppure un nuovo "Start", se il
    ciclo è stato interrotto). I log sono in ordine cronologico.
    """
    base = Log.objects.all()
    if macchina:
        base = base.filter(macchine=macchina)

    try:
        id_ordine = float(ordine.id_ordine_esterno)
    except (TypeError, ValueError):
        return None, []

    cicli = base.filter(attività__tipo_attività=STATO_CICLO, input=1)
    start = (cicli.filter(descrizione__startswith=PREFISSO_START_CICLO, valore=id_ordine)
             .order_by('-timestamp', '-id').first())
    if start:
        fine = cicli.filter(timestamp__gt=start.timestamp).order_by('timestamp', 'id').first()
        finestra = base.filter(timestamp__gt=start.timestamp)
        if fine:
            finestra = finestra.filter(timestamp__lt=fine.timestamp)
    elif ordine.data_inizio and ordine.data_fine:
        # Start ciclo senza ID ordine (vecchio firmware): finestra DataInizio-DataFine dell'ordine.
        # Le date dell'ordine sono al minuto, quindi si estende la fine al minuto successivo.
        finestra = base.filter(timestamp__gte=ordine.data_inizio,
                               timestamp__lt=ordine.data_fine + timedelta(minutes=1))
    else:
        # Dati importati in passato: intervallo tra il primo e l'ultimo log con valore = id ordine
        marcatori = base.filter(valore=id_ordine).order_by('timestamp')
        if not marcatori.exists():
            return None, []
        finestra = base.filter(timestamp__gt=marcatori.first().timestamp,
                               timestamp__lt=marcatori.last().timestamp)
    return start, list(finestra.select_related('attività').order_by('timestamp', 'id'))


def estrai_movimenti(logs):
    """Quote comandate di Sponda (X) e Carro (Y) e, per ogni movimento del Carro,
    l'angolo dell'Arco letto subito prima della partenza e subito dopo l'arrivo."""
    quote_x, quote_y, angoli = [], [], []
    for indice, log in enumerate(logs):
        tipo = log.attività.tipo_attività
        if log.input != 1 or tipo not in (MOV_X, MOV_Y):
            continue
        if tipo == MOV_X:
            quote_x.append(log.valore)
            continue

        quote_y.append(log.valore)
        prima = next((l.valore for l in reversed(logs[:indice]) if l.attività.tipo_attività == MOV_ALPHA), None)
        # fine del movimento: "Quota Carro ... Raggiunta" (se assente si usa la partenza)
        arrivo = next((j for j in range(indice + 1, len(logs))
                       if logs[j].attività.tipo_attività == MOV_Y and logs[j].input == 0
                       and 'raggiunt' in (logs[j].descrizione or '').lower()), indice)
        dopo = next((l.valore for l in logs[arrivo + 1:] if l.attività.tipo_attività == MOV_ALPHA), None)
        angoli.append((prima, dopo))
    return quote_x, quote_y, angoli


def distanza_pezzo(quote, i):
    """Corsa relativa al pezzo i-esimo: differenza con la quota successiva (o precedente per l'ultima)."""
    if i < len(quote) - 1:
        return abs(quote[i] - quote[i + 1])
    return abs(quote[i - 1] - quote[i]) if i > 0 else 0


class ProcessQRCodeView(LoginRequiredMixin, View):
    template_name = 'storico.html'

    def get(self, request):
        codice = leggi_codice_qr(request.GET.get('qr_data'))
        commesse = (Commessa.objects.filter(id_record=codice)
                    .select_related('ordine').order_by('ordine__id_ordine_esterno', 'id'))
        if not codice or not commesse.exists():
            return render(request, self.template_name, {'error': 'Nessuna commessa trovata.'})

        macchine = []
        ordini = []
        articoli = []
        cliente = ''
        scartox = scartoy = 'Non calcolato'
        qualità = "Nessun log trovato per il valore specificato."

        for commessa in commesse:
            cliente = nome_cliente(commessa.cliente)
            macchina = Macchina.objects.filter(identificativo=commessa.id_macchina).first()
            macchine.append(macchina)

            ordine = commessa.ordine
            if not ordine:
                continue
            ordini.append(ordine)
            for articolo in ordine.articoli.all():
                altezza_m = articolo.altezza / 1000
                larghezza_m = articolo.larghezza / 1000
                spessore_m = articolo.spessore / 1000
                volume = altezza_m * larghezza_m * spessore_m
                densità = articolo.peso / volume if volume > 0 else 0

                articoli.append({
                    'codice': articolo.codice,
                    'altezza': altezza_m,
                    'larghezza': larghezza_m,
                    'spessore': spessore_m,
                    'peso': articolo.peso,
                    'densità': densità,
                    'altezzamm': articolo.altezza,
                    'larghezzamm': articolo.larghezza,
                    'spessoremm': articolo.spessore,
                })

            # Controllo qualità
            start, logs = log_ciclo_ordine(ordine, macchina)
            if not logs:
                qualità = "Nessun log trovato per il valore specificato."
                continue

            quote_x, quote_y, angoli = estrai_movimenti(logs)
            pezzo = commessa.qtalav or 0
            dima_testo = commessa.dima
            if not dima_testo and start and start.lunghezza is not None and start.larghezza is not None:
                # Riga ordine senza sagoma NEXUM: misure programmate nello start del ciclo
                dima_testo = f"{start.lunghezza:g}X{start.larghezza:g}"
            dima = re.split(r'[xX]', dima_testo or '')
            if (pezzo < 1 or pezzo > min(len(quote_x), len(quote_y), len(angoli))
                    or len(dima) < 2 or commessa.profondità is None):
                qualità = "Dati insufficienti per calcolare la qualità"
                continue

            # Valutazione sul pezzo n. qtalav (ultimo lavorato), come in precedenza
            i = pezzo - 1
            new_valx = distanza_pezzo(quote_x, i)
            new_valy = distanza_pezzo(quote_y, i)
            angolo_prima, angolo_dopo = angoli[i]
            if angolo_prima is None or angolo_dopo is None:
                qualità = "Dati insufficienti per calcolare la qualità"
                continue
            vala = abs(angolo_prima)
            new_vala = abs(angolo_dopo)
            media_vala = abs(angolo_prima + angolo_dopo) / 2

            try:
                dima_y = float(dima[0])
            except ValueError:
                qualità = "Dati insufficienti per calcolare la qualità"
                continue
            dima_z = commessa.profondità
            scartox = new_valx - dima_z
            scartoy = new_valy - dima_y
            # Il confronto con il pezzo precedente non era mai attivo (valori 99999): comportamento invariato
            qualità = self.calcola_qualità(scartox, scartoy, dima_z, new_vala, vala, media_vala, 99999, 99999)

        context = {
            'codice': codice,
            'commesse': commesse,
            'macchine': macchine,
            'ordini': ordini,
            'articoli': articoli,
            'cliente': cliente,
            'scartoy': scartoy,
            'scartox': scartox,
            'qualità': qualità,
        }

        return render(request, self.template_name, context)

    def calcola_qualità(self, scartox, scartoy, dima_z, new_vala, vala, media_vala, scartox_left, scartoy_left ):

        qualità_angolo = QualitàAngoloAutomatico.objects.first()
        soglia_accettabile = QualitàTaglio.objects.values_list('soglia_accettabile', flat=True).first()
        soglia_ottimo = qualità_angolo.soglia_ottimo if qualità_angolo else None
        soglia_rettifica = qualità_angolo.soglia_rettifica if qualità_angolo else None

        if soglia_accettabile is None or soglia_ottimo is None or soglia_rettifica is None:
            return "Soglie di qualità non configurate"

        limite_x = dima_z * soglia_accettabile

        if vala <= soglia_ottimo and new_vala <= soglia_ottimo and media_vala <= soglia_ottimo:
            stato = "Ottimo"
        elif vala > soglia_ottimo and new_vala <= soglia_ottimo and media_vala <= soglia_ottimo:
            stato = "Ottimo"
        elif vala <= soglia_ottimo and new_vala > soglia_ottimo and media_vala <= soglia_ottimo:
            stato = "Ottimo"
        elif vala > soglia_ottimo and new_vala > soglia_ottimo and media_vala <= soglia_ottimo:
            stato = "Ottimo"
        elif soglia_rettifica > media_vala > soglia_ottimo:
            stato = "Rettificare"
        else:
            stato = "Scartare"

        if scartox <= 0:
            # 3 casi per la X
            if abs(scartox) <= abs(limite_x) and scartoy >= 0 and stato == "Ottimo":
                statoparziale = "Ottimo"
            elif abs(scartox) <= abs(limite_x) and scartoy >= 0 and stato == "Rettificare":
                statoparziale = "Rettificare"
            elif abs(scartox) <= abs(limite_x) and scartoy >= 0 and stato == "Scartare":
                statoparziale = "Scartare"
            # 3 casi per Y
            elif abs(scartox) > abs(limite_x) and scartoy >= 0 and stato == "Ottimo":
                statoparziale = "Ottimo"
            elif abs(scartox) > abs(limite_x) and scartoy >= 0 and stato == "Rettificare":
                statoparziale = "Rettificare"
            elif abs(scartox) > abs(limite_x) and scartoy >= 0 and stato == "Scartare":
                statoparziale = "Scartare"
            else:
                statoparziale = "Scartare"
        else:
            statoparziale = "Scartare"


        if scartox_left != 99999 and scartoy_left != 99999:
            if scartox_left <= 0 and scartoy_left != 99999:
                # casi per la X precedente
                if abs(scartox_left) <= abs(limite_x) and scartoy_left >= 0 and statoparziale == "Ottimo":
                    return "Ottimo"
                elif abs(scartox_left) <= abs(limite_x) and scartoy_left >= 0 and statoparziale == "Rettificare":
                    return "Rettificare"
                elif abs(scartox_left) <= abs(limite_x) and scartoy_left >= 0 and statoparziale == "Scartare":
                    return "Scartare"
                # casi per Y precedente
                elif abs(scartox_left) > abs(limite_x) and scartoy_left >= 0 and statoparziale == "Ottimo":
                    return "Ottimo"
                elif abs(scartox_left) > abs(limite_x) and scartoy_left >= 0 and statoparziale == "Rettificare":
                    return "Rettificare"
                elif abs(scartox_left) > abs(limite_x) and scartoy_left >= 0 and statoparziale == "Scartare":
                    return "Scartare"
                else:
                    return "Scartare"
            else:
                return "Scartare"
        else:
            return statoparziale
