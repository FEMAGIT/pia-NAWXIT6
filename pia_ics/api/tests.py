from datetime import date, datetime, time, timedelta, timezone as dt_timezone

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from autenticazione.models import ApiToken, Cliente, CustomUser
from struttura.models import (Articolo, Assistenza, Attività, Classificazione, Commessa, Lavorazione, Log, Macchina,
                              Manutenzione, Ordine, OrdiniBlocco, QualitàAngoloAutomatico, QualitàTaglio,
                              SerialeArticolo, TipoMacchina, TipoManutenzione)

UTC = dt_timezone.utc


def url(nome, *args):
    return reverse(f'api:{nome}', args=args)


class ApiBase(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.admin = CustomUser.objects.create_superuser('admin', 'admin@example.com', 'pw')
        cls.worker = CustomUser.objects.create_user('worker', 'worker@example.com', 'pw', role='maintenance_worker')
        cls.cliente_a_user = CustomUser.objects.create_user('ca', 'ca@example.com', 'pw', role='client')
        cls.cliente_b_user = CustomUser.objects.create_user('cb', 'cb@example.com', 'pw', role='client')

        cls.cliente_a = Cliente.objects.create(ragione_sociale='Alfa', p_iva='11111111111', email='a@a.it',
                                               cf='AAAAAAAAAAAAAAAA', sede_legale='Roma')
        cls.cliente_b = Cliente.objects.create(ragione_sociale='Beta', p_iva='22222222222', email='b@b.it',
                                               cf='BBBBBBBBBBBBBBBB', sede_legale='Milano')
        cls.cliente_a.users.add(cls.cliente_a_user)
        cls.cliente_b.users.add(cls.cliente_b_user)

        cls.tipo = TipoMacchina.objects.create(tipomacchina='TAGLIO', desctipomacchina='Taglio')
        cls.tipo_b = TipoMacchina.objects.create(tipomacchina='FRESA', desctipomacchina='Fresa')
        cls.macchina_a = Macchina.objects.create(tipo_macchina=cls.tipo, desctipomacchina='Taglio', identificativo='M-A',
                                                 descrmacchina='Macchina Alfa', cliente=cls.cliente_a)
        cls.macchina_b = Macchina.objects.create(tipo_macchina=cls.tipo_b, desctipomacchina='Fresa', identificativo='M-B',
                                                 descrmacchina='Macchina Beta', cliente=cls.cliente_b)

        tm = TipoManutenzione.objects.create(tipomanutenzione='meccanico', settore='Meccanica')
        cls.manutenzione_a = Manutenzione.objects.create(componente='Lama', descrizionecomponente='Lama circolare',
                                                         tipo_manutenzione=tm, tipo_macchina=cls.tipo)
        Manutenzione.objects.create(componente='Fresa', descrizionecomponente='Fresa', tipo_manutenzione=tm,
                                    tipo_macchina=cls.tipo_b)
        SerialeArticolo.objects.create(codice_interno='S1', manutenzione=cls.manutenzione_a)

        cls.assistenza_a = Assistenza.objects.create(titolo='Guasto A', descassistenza='x', data=date(2026, 3, 10),
                                                     ora_inizio=time(9, 0), macchine=cls.macchina_a, stato='aperto')
        cls.assistenza_b = Assistenza.objects.create(titolo='Guasto B', descassistenza='y', data=date(2026, 3, 11),
                                                     ora_inizio=time(10, 0), macchine=cls.macchina_b, stato='chiuso')
        Classificazione.objects.create(assistenza=cls.assistenza_a, manutenzione=cls.manutenzione_a)

        cls.ordine_a = Ordine.objects.create(descordine='Ordine A', dataconsegna=date(2026, 4, 1), materiale='PU',
                                             id_ordine_esterno='2600028')
        cls.ordine_b = Ordine.objects.create(descordine='Ordine B', dataconsegna=date(2026, 4, 2), materiale='PU',
                                             id_ordine_esterno='2600029')
        cls.commessa_a = Commessa.objects.create(ordine=cls.ordine_a, id_macchina='M-A', codicecommessa='C-A',
                                                 descrizione='d', id_record='262', cliente='501.001 ALFA SPA',
                                                 dima='430X60', profondità=60, qtalav=1, qta=2)
        cls.commessa_b = Commessa.objects.create(ordine=cls.ordine_b, id_macchina='M-B', codicecommessa='C-B',
                                                 descrizione='d', id_record='300', cliente='Beta', qta=1)
        cls.articolo_a = Articolo.objects.create(tipo='BLK', codice='ART-A', altezza=1000, larghezza=1000,
                                                 spessore=1000, peso=30, data_creazione=timezone.now())
        OrdiniBlocco.objects.create(articolo=cls.articolo_a, ordine=cls.ordine_a)

        cls.lavorazione_a = Lavorazione.objects.create(macchina=cls.macchina_a, commessa=cls.commessa_a,
                                                       timestamp=datetime(2026, 4, 1, 8, tzinfo=UTC))
        Lavorazione.objects.create(macchina=cls.macchina_b, commessa=cls.commessa_b,
                                   timestamp=datetime(2026, 4, 2, 8, tzinfo=UTC))

        cls.att_ciclo = Attività.objects.create(tipo_attività='Stato ciclo Automatico')
        cls.att_x = Attività.objects.create(tipo_attività='Movimentazione x')
        base = datetime(2026, 4, 1, 8, tzinfo=UTC)
        cls.log_start = Log.objects.create(
            macchine=cls.macchina_a, attività=cls.att_ciclo, timestamp=base, input=1, output=0, valore=2600028,
            descrizione='Start Ciclo Automatico ID_Ordine 2600028 (430.00 x 60.00 mm)')
        Log.objects.create(macchine=cls.macchina_a, attività=cls.att_x, timestamp=base + timedelta(minutes=1),
                           input=1, output=0, valore=60.0, descrizione='Start Movimentazione Sponda alla quota 60.00 mm')
        Log.objects.create(macchine=cls.macchina_b, attività=cls.att_x, timestamp=base + timedelta(minutes=2),
                           input=1, output=0, valore=10.0, descrizione='Start Movimentazione Sponda alla quota 10.00 mm')

    def get(self, nome, *args, user=None, **params):
        client = self.client
        if user is not None:
            _, chiave = ApiToken.crea(user, 'test')
            return client.get(url(nome, *args), params, HTTP_AUTHORIZATION=f'Bearer {chiave}')
        return client.get(url(nome, *args), params)

    def ids(self, risposta):
        return {r['id'] for r in risposta.json()['results']}


class AutenticazioneTest(ApiBase):
    def test_senza_credenziali_401(self):
        r = self.get('macchine')
        self.assertEqual(r.status_code, 401)
        self.assertEqual(r.json()['error']['code'], 'non_autenticato')
        self.assertEqual(r['WWW-Authenticate'], 'Bearer')

    def test_token_errato_401(self):
        r = self.client.get(url('macchine'), HTTP_AUTHORIZATION='Bearer sbagliato')
        self.assertEqual((r.status_code, r.json()['error']['code']), (401, 'token_non_valido'))

    def test_schema_non_bearer_401(self):
        r = self.client.get(url('macchine'), HTTP_AUTHORIZATION='Basic abc')
        self.assertEqual(r.status_code, 401)

    def test_token_valido_e_ultimo_uso(self):
        token, chiave = ApiToken.crea(self.admin, 'prova')
        self.assertNotIn(chiave, token.key_hash)
        r = self.client.get(url('me'), HTTP_AUTHORIZATION=f'Bearer {chiave}')
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()['email'], 'admin@example.com')
        token.refresh_from_db()
        self.assertIsNotNone(token.ultimo_uso)

    def test_token_disattivato_scaduto_o_utente_inattivo(self):
        token, chiave = ApiToken.crea(self.admin, 'prova')
        intestazione = {'HTTP_AUTHORIZATION': f'Bearer {chiave}'}
        token.attivo = False
        token.save()
        self.assertEqual(self.client.get(url('me'), **intestazione).status_code, 401)
        token.attivo, token.scadenza = True, timezone.now() - timedelta(seconds=1)
        token.save()
        self.assertEqual(self.client.get(url('me'), **intestazione).status_code, 401)
        token.scadenza = None
        token.save()
        self.admin.is_active = False
        self.admin.save()
        self.assertEqual(self.client.get(url('me'), **intestazione).status_code, 401)

    def test_sessione_web_accettata(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(url('macchine')).status_code, 200)

    def test_solo_lettura(self):
        _, chiave = ApiToken.crea(self.admin, 'prova')
        r = self.client.post(url('macchine'), {}, HTTP_AUTHORIZATION=f'Bearer {chiave}')
        self.assertEqual(r.status_code, 405)
        self.assertEqual(r['Allow'], 'GET, HEAD')

    def test_sessione_non_soggetta_a_csrf_in_scrittura(self):
        # una POST con sessione non deve né passare né richiedere CSRF: sempre 405 JSON
        self.client.force_login(self.admin)
        self.assertEqual(self.client.post(url('macchine'), {}).status_code, 405)


class PerimetroTest(ApiBase):
    def test_admin_e_manutentore_vedono_tutto(self):
        for utente in (self.admin, self.worker):
            self.assertEqual(self.ids(self.get('macchine', user=utente)), {self.macchina_a.id, self.macchina_b.id})
            self.assertEqual(self.get('me', user=utente).json()['accesso_completo'], True)

    def test_cliente_vede_solo_le_sue_macchine(self):
        self.assertEqual(self.ids(self.get('macchine', user=self.cliente_a_user)), {self.macchina_a.id})
        self.assertEqual(self.get('macchina_dettaglio', self.macchina_b.id, user=self.cliente_a_user).status_code, 404)
        self.assertEqual(self.get('cliente_dettaglio', self.cliente_b.id, user=self.cliente_a_user).status_code, 404)
        self.assertEqual(self.ids(self.get('clienti', user=self.cliente_a_user)), {self.cliente_a.id})

    def test_cliente_dati_collegati(self):
        u = self.cliente_a_user
        self.assertEqual(self.ids(self.get('assistenze', user=u)), {self.assistenza_a.id})
        self.assertEqual(self.get('assistenza_dettaglio', self.assistenza_b.id, user=u).status_code, 404)
        self.assertEqual(self.get('assistenza_chat', self.assistenza_b.id, user=u).status_code, 404)
        self.assertEqual(self.ids(self.get('ordini', user=u)), {self.ordine_a.id})
        self.assertEqual(self.ids(self.get('commesse', user=u)), {self.commessa_a.id})
        self.assertEqual(self.ids(self.get('lavorazioni', user=u)), {self.lavorazione_a.id})
        self.assertEqual(self.ids(self.get('tipi_macchina', user=u)), {self.tipo.id})
        self.assertEqual(self.get('tipo_macchina_dettaglio', self.tipo_b.id, user=u).status_code, 404)
        self.assertEqual({r['componente'] for r in self.get('manutenzioni', user=u).json()['results']}, {'Lama'})
        log_visti = {r['macchina_id'] for r in self.get('log', user=u).json()['results']}
        self.assertEqual(log_visti, {self.macchina_a.id})
        self.assertEqual(self.get('articolo_dettaglio', self.articolo_a.id, user=self.cliente_b_user).status_code, 404)
        self.assertEqual(self.get('ordine_dettaglio', self.ordine_b.id, user=u).status_code, 404)
        self.assertEqual(self.get('ordine_ciclo', self.ordine_b.id, user=u).status_code, 404)

    def test_cliente_senza_clienti_associati_non_vede_nulla(self):
        orfano = CustomUser.objects.create_user('orfano', 'o@example.com', 'pw', role='client')
        self.assertEqual(self.get('macchine', user=orfano).json()['count'], 0)
        self.assertEqual(self.get('log', user=orfano).json()['count'], 0)

    def test_tracciabilita_limitata_al_perimetro(self):
        self.assertEqual(self.get('tracciabilita', user=self.cliente_b_user, qr_data='262/1').status_code, 404)
        self.assertEqual(self.get('tracciabilita', user=self.cliente_a_user, qr_data='262/1').status_code, 200)


class ListeTest(ApiBase):
    def test_paginazione(self):
        r = self.get('log', user=self.admin, page_size=2).json()
        self.assertEqual((r['count'], r['page'], r['page_size'], r['num_pages'], len(r['results'])), (3, 1, 2, 2, 2))
        r2 = self.get('log', user=self.admin, page_size=2, page=2).json()
        self.assertEqual(len(r2['results']), 1)
        self.assertEqual(len(self.get('log', user=self.admin, page_size=2, page=9).json()['results']), 0)

    def test_parametri_non_validi_400(self):
        for params in ({'page_size': 0}, {'page_size': 99999}, {'page': 'x'}, {'page': 0}, {'da': 'ieri'},
                       {'ordinamento': 'descrizione'}, {'macchina': 'abc'}):
            r = self.get('log', user=self.admin, **params)
            self.assertEqual((r.status_code, r.json()['error']['code']), (400, 'parametro_non_valido'), params)

    def test_log_filtri(self):
        u = self.admin
        self.assertEqual(self.get('log', user=u, macchina=self.macchina_a.id).json()['count'], 2)
        self.assertEqual(self.get('log', user=u, tipo_attivita='Movimentazione x').json()['count'], 2)
        self.assertEqual(self.get('log', user=u, da='2026-04-01T08:01:30Z').json()['count'], 1)
        self.assertEqual(self.get('log', user=u, a='2026-04-01').json()['count'], 3)  # tutta la giornata
        self.assertEqual(self.get('log', user=u, a='2026-03-31').json()['count'], 0)
        self.assertEqual(self.get('log', user=u, q='Sponda').json()['count'], 2)

    def test_log_ordinamento_e_campi(self):
        r = self.get('log', user=self.admin, ordinamento='-timestamp').json()['results']
        self.assertEqual(r[0]['valore'], 10.0)
        primo = self.get('log', user=self.admin).json()['results'][0]
        self.assertEqual(primo['tipo_attivita'], 'Stato ciclo Automatico')
        self.assertEqual(primo['timestamp'], '2026-04-01T08:00:00+00:00')

    def test_macchine_filtri(self):
        u = self.admin
        self.assertEqual(self.ids(self.get('macchine', user=u, cliente=self.cliente_b.id)), {self.macchina_b.id})
        self.assertEqual(self.ids(self.get('macchine', user=u, q='alfa')), {self.macchina_a.id})
        m = self.get('macchina_dettaglio', self.macchina_a.id, user=u).json()
        self.assertEqual(m['tipo_macchina']['codice'], 'TAGLIO')
        self.assertEqual(m['cliente']['ragione_sociale'], 'Alfa')

    def test_sotto_risorse_macchina(self):
        u = self.admin
        man = self.get('macchina_manutenzioni', self.macchina_a.id, user=u).json()['results']
        self.assertEqual([(m['componente'], m['seriali'][0]['codice_interno']) for m in man], [('Lama', 'S1')])
        self.assertEqual(self.ids(self.get('macchina_assistenze', self.macchina_a.id, user=u)), {self.assistenza_a.id})
        self.assertEqual(self.get('macchina_documenti', self.macchina_a.id, user=u).json()['count'], 0)

    def test_assistenze(self):
        u = self.admin
        self.assertEqual(self.ids(self.get('assistenze', user=u, stato='chiuso')), {self.assistenza_b.id})
        self.assertEqual(self.ids(self.get('assistenze', user=u, da='2026-03-11')), {self.assistenza_b.id})
        d = self.get('assistenza_dettaglio', self.assistenza_a.id, user=u).json()
        self.assertEqual((d['fascia_oraria'], d['stato_descrizione']), ('09:00', 'Aperto'))
        self.assertEqual(d['classificazioni'][0]['manutenzione']['componente'], 'Lama')
        self.assertEqual(self.get('assistenze', user=u, da='boh').status_code, 400)

    def test_calendario_senza_dettagli(self):
        r = self.get('calendario', user=self.cliente_a_user).json()
        self.assertEqual(r['occupati_per_giorno'], {'2026-03-10': ['09:00'], '2026-03-11': ['10:00']})
        self.assertEqual(len(r['fasce']), 6)
        self.assertNotIn('Guasto', str(r))

    def test_ordine_commessa_articolo(self):
        u = self.admin
        o = self.get('ordine_dettaglio', self.ordine_a.id, user=u).json()
        self.assertEqual([c['codice_commessa'] for c in o['commesse']], ['C-A'])
        self.assertEqual(o['commesse'][0]['cliente_nome'], 'ALFA SPA')
        self.assertEqual([a['codice'] for a in o['articoli']], ['ART-A'])
        self.assertEqual(self.ids(self.get('commesse', user=u, id_record='300')), {self.commessa_b.id})
        a = self.get('articolo_dettaglio', self.articolo_a.id, user=u).json()
        self.assertEqual((a['volume_m3'], a['densita_kg_m3']), (1.0, 30.0))
        self.assertEqual(self.ids(self.get('articoli', user=u, ordine=self.ordine_b.id)), set())

    def test_lavorazioni_e_attivita(self):
        u = self.admin
        self.assertEqual(self.get('lavorazioni', user=u, macchina=self.macchina_a.id).json()['count'], 1)
        self.assertEqual({a['tipo'] for a in self.get('attivita', user=u).json()['results']},
                         {'Stato ciclo Automatico', 'Movimentazione x'})

    def test_ciclo_ordine(self):
        r = self.get('ordine_ciclo', self.ordine_a.id, user=self.admin).json()
        self.assertEqual(r['start']['id'], self.log_start.id)
        self.assertEqual(len(r['log']), 1)
        self.assertEqual(r['movimenti']['quote_sponda_x'], [60.0])
        self.assertEqual(r['macchina_id'], self.macchina_a.id)

    def test_indice_e_me(self):
        r = self.get('indice', user=self.admin).json()
        self.assertEqual(r['versione'], 'v1')
        self.assertIn('/api/v1/log', [e['percorso'] for e in r['endpoint']])
        me = self.get('me', user=self.cliente_a_user).json()
        self.assertEqual((me['ruolo'], me['accesso_completo'], me['clienti'][0]['id']),
                         ('client', False, self.cliente_a.id))


class TracciabilitaTest(ApiBase):
    def test_parametro_obbligatorio_e_non_trovato(self):
        self.assertEqual(self.get('tracciabilita', user=self.admin).status_code, 400)
        self.assertEqual(self.get('tracciabilita', user=self.admin, qr_data='999/1').status_code, 404)

    def test_senza_soglie_configurate(self):
        r = self.get('tracciabilita', user=self.admin, qr_data='IdRecord:262/1')
        self.assertEqual(r.status_code, 200)
        d = r.json()
        self.assertEqual((d['codice'], d['pezzo'], d['cliente']), ('262', 1, 'ALFA SPA'))
        self.assertEqual(d['commesse'][0]['macchina']['identificativo'], 'M-A')
        self.assertEqual(d['commesse'][0]['ordine']['id_ordine_esterno'], '2600028')
        self.assertEqual(d['articoli'][0]['codice'], 'ART-A')
        self.assertFalse(d['qualita_valutata'])
        self.assertIsNone(d['scarto_x_mm'])

    def test_qualita_calcolata(self):
        QualitàAngoloAutomatico.objects.create(soglia_ottimo=0.5, soglia_rettifica=1.0)
        QualitàTaglio.objects.create(soglia_accettabile=0.1)
        base = datetime(2026, 4, 1, 8, tzinfo=UTC)
        att_y = Attività.objects.create(tipo_attività='Movimentazione y')
        att_a = Attività.objects.create(tipo_attività='Movimentazione alpha')
        sequenza = [
            (att_a, 0, 0, 0.1, 'Feedback Accelerometro Arco 0.10 °'),
            (self.att_x, 1, 0, 60.0, 'Start Movimentazione Sponda alla quota 60.00 mm'),
            (att_y, 1, 0, 0.0, 'Start Movimentazione Carro alla quota 0.00 mm'),
            (att_y, 0, 1, 430.0, 'Quota Carro 430.00 mm Raggiunta'),
            (att_a, 0, 0, 0.1, 'Feedback Accelerometro Arco 0.10 °'),
        ]
        for i, (att, inp, out, valore, testo) in enumerate(sequenza, start=2):
            Log.objects.create(macchine=self.macchina_a, attività=att, timestamp=base + timedelta(minutes=i),
                               input=inp, output=out, valore=valore, descrizione=testo)
        d = self.get('tracciabilita', user=self.admin, qr_data='262/1').json()
        self.assertEqual(d['commesse'][0]['controllo_qualita']['esito'], d['qualita'])
        self.assertIn(d['qualita'], ('Ottimo', 'Rettificare', 'Scartare'))
        self.assertTrue(d['qualita_valutata'])
        self.assertIsNotNone(d['scarto_x_mm'])

    def test_soglie(self):
        self.assertEqual(self.get('soglie_qualita', user=self.admin).json(),
                         {'angolo_automatico': None, 'taglio': None})
        QualitàTaglio.objects.create(soglia_accettabile=0.1)
        self.assertEqual(self.get('soglie_qualita', user=self.admin).json()['taglio'], {'soglia_accettabile': 0.1})


class CasiAggiuntiviTest(ApiBase):
    def test_head_consentito(self):
        _, chiave = ApiToken.crea(self.admin, 'prova')
        r = self.client.head(url('macchine'), HTTP_AUTHORIZATION=f'Bearer {chiave}')
        self.assertEqual(r.status_code, 200)

    def test_metodi_di_scrittura_rifiutati_su_ogni_endpoint(self):
        _, chiave = ApiToken.crea(self.admin, 'prova')
        for metodo in ('post', 'put', 'patch', 'delete'):
            r = getattr(self.client, metodo)(url('log'), HTTP_AUTHORIZATION=f'Bearer {chiave}')
            self.assertEqual(r.status_code, 405, metodo)

    def test_chat_in_ordine_cronologico_con_allegato(self):
        from struttura.models import Chat
        Chat.objects.create(messaggio='secondo', assistenze=self.assistenza_a, utentecorrente='u',
                            datacorrente=datetime(2026, 3, 10, 10, tzinfo=UTC), is_staff=True)
        Chat.objects.create(messaggio='primo', assistenze=self.assistenza_a, utentecorrente='u',
                            datacorrente=datetime(2026, 3, 10, 9, tzinfo=UTC), preventivo='prev.pdf', is_staff=False)
        r = self.get('assistenza_chat', self.assistenza_a.id, user=self.cliente_a_user).json()['results']
        self.assertEqual([m['messaggio'] for m in r], ['primo', 'secondo'])
        self.assertTrue(r[0]['allegato'].startswith('http://testserver/'))
        self.assertIsNone(r[1]['allegato'])

    def test_documenti_con_url_assoluto_e_perimetro(self):
        from struttura.models import Documento
        Documento.objects.create(nome_documento='Manuale A', path_documento='documenti/a.pdf', tipo_macchina=self.tipo)
        Documento.objects.create(nome_documento='Manuale B', tipo_macchina=self.tipo_b)
        r = self.get('documenti', user=self.cliente_a_user).json()['results']
        self.assertEqual([(d['nome'], d['file']) for d in r],
                         [('Manuale A', 'http://testserver/media/documenti/a.pdf')])
        self.assertEqual(self.get('documenti', user=self.admin).json()['count'], 2)

    def test_formati_qr_equivalenti(self):
        riferimento = self.get('tracciabilita', user=self.admin, qr_data='262/1').json()
        for formato in ('IdRecord:262/1', 'id:262/1', ' id : 262/1 '):
            self.assertEqual(self.get('tracciabilita', user=self.admin, qr_data=formato).json(), riferimento, formato)
        senza_pezzo = self.get('tracciabilita', user=self.admin, qr_data='262').json()
        self.assertIsNone(senza_pezzo['pezzo'])

    def test_numero_query_costante_sulle_liste(self):
        _, chiave = ApiToken.crea(self.admin, 'prova')
        intestazione = {'HTTP_AUTHORIZATION': f'Bearer {chiave}'}
        from django.db import connection
        from django.test.utils import CaptureQueriesContext
        self.client.get(url('me'), **intestazione)  # il primo uso aggiorna ultimo_uso: lo escludiamo dal confronto
        for nome in ('log', 'macchine', 'assistenze', 'commesse', 'lavorazioni'):
            with self.subTest(nome):
                with CaptureQueriesContext(connection) as piccola:
                    self.client.get(url(nome), {'page_size': 1}, **intestazione)
                with CaptureQueriesContext(connection) as grande:
                    self.client.get(url(nome), {'page_size': 500}, **intestazione)
                self.assertEqual(len(piccola), len(grande), f'{nome}: query dipendenti dal numero di righe (N+1)')

    def test_cliente_non_vede_log_di_altri_neanche_via_filtro(self):
        r = self.get('log', user=self.cliente_a_user, macchina=self.macchina_b.id).json()
        self.assertEqual(r['count'], 0)
        r = self.get('assistenze', user=self.cliente_a_user, cliente=self.cliente_b.id).json()
        self.assertEqual(r['count'], 0)

    def test_data_ora_senza_fuso_interpretata_in_utc(self):
        self.assertEqual(self.get('log', user=self.admin, da='2026-04-01T08:01:00').json()['count'], 2)
        self.assertEqual(self.get('log', user=self.admin, da='2026-04-01 08:01:00').json()['count'], 2)

    def test_risposta_json_con_caratteri_accentati(self):
        Assistenza.objects.create(titolo='Perché è rotto', descassistenza='già', macchine=self.macchina_a)
        r = self.client.get(url('assistenze'), {'q': 'Perché'},
                            HTTP_AUTHORIZATION='Bearer ' + ApiToken.crea(self.admin, 'p')[1])
        self.assertIn('Perché è rotto', r.content.decode('utf-8'))
        self.assertIn('application/json', r['Content-Type'])


class ComandoCreaTokenTest(ApiBase):
    def test_crea_token_e_lo_si_puo_usare(self):
        from io import StringIO
        from django.core.management import call_command
        out = StringIO()
        call_command('crea_token_api', 'worker@example.com', '--nome', 'ERP', '--giorni', '30', stdout=out)
        chiave = out.getvalue().strip().splitlines()[-1]
        token = ApiToken.objects.get(nome='ERP')
        self.assertEqual(token.user, self.worker)
        self.assertEqual(token.key_hash, ApiToken.calcola_hash(chiave))
        self.assertGreater(token.scadenza, timezone.now() + timedelta(days=29))
        self.assertEqual(self.client.get(url('me'), HTTP_AUTHORIZATION=f'Bearer {chiave}').status_code, 200)

    def test_utente_inesistente(self):
        from django.core.management import call_command
        from django.core.management.base import CommandError
        with self.assertRaises(CommandError):
            call_command('crea_token_api', 'nessuno@example.com')


class DettagliTest(ApiBase):
    def test_dettagli_per_amministratore_e_cliente_proprietario(self):
        casi = [
            ('cliente_dettaglio', self.cliente_a.id, 'ragione_sociale', 'Alfa'),
            ('tipo_macchina_dettaglio', self.tipo.id, 'codice', 'TAGLIO'),
            ('manutenzione_dettaglio', self.manutenzione_a.id, 'componente', 'Lama'),
            ('commessa_dettaglio', self.commessa_a.id, 'codice_commessa', 'C-A'),
            ('articolo_dettaglio', self.articolo_a.id, 'codice', 'ART-A'),
        ]
        for nome, pk, campo, atteso in casi:
            for utente in (self.admin, self.cliente_a_user):
                with self.subTest(nome=nome, utente=utente.username):
                    r = self.get(nome, pk, user=utente)
                    self.assertEqual(r.status_code, 200)
                    self.assertEqual(r.json()[campo], atteso)
            self.assertEqual(self.get(nome, 999999, user=self.admin).status_code, 404, nome)

    def test_manutenzione_dettaglio_ha_seriali_e_clienti_elenco(self):
        d = self.get('manutenzione_dettaglio', self.manutenzione_a.id, user=self.admin).json()
        self.assertEqual(d['seriali'][0]['codice_interno'], 'S1')
        self.assertEqual(self.ids(self.get('clienti', user=self.admin)), {self.cliente_a.id, self.cliente_b.id})
        self.assertEqual(self.ids(self.get('clienti', user=self.admin, q='beta')), {self.cliente_b.id})
