from types import SimpleNamespace
from unittest import mock

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse

from autenticazione.models import Cliente, CustomUser
from struttura.models import (Assistenza, Classificazione, Macchina, Manutenzione, SerialeArticolo,
                              TipoMacchina, TipoManutenzione)

from struttura.fema import (MOV_ALPHA, MOV_X, MOV_Y, STATO_CICLO, STATO_LAMA, formatta_misura,
                            id_record_da_note, interpreta_log)


class InterpretaLogTest(SimpleTestCase):
    """Le regole devono coincidere con la vista PIA_FEMA.dbo.LOGS_TipoAttivita_4."""

    def test_start_ciclo_con_ordine_e_misure(self):
        log = interpreta_log("Start Ciclo Automatico ID_Ordine 2600028 (2359.96 x 75.00 mm)")
        self.assertEqual(log.tipo_attivita, STATO_CICLO)
        self.assertEqual((log.input, log.output), (1, 0))
        self.assertEqual(log.valore, 2600028)
        self.assertEqual((log.lunghezza, log.larghezza), (2359.96, 75.0))
        self.assertEqual(log.unita_misura, "mm")

    def test_fine_ciclo(self):
        log = interpreta_log("Ciclo Automatico ID Ordine 2600028 Terminato Durata 00:02:11")
        self.assertEqual((log.tipo_attivita, log.input, log.valore), (STATO_CICLO, 1, 2600028))

    def test_sponda_e_asse_x_carro_e_asse_y(self):
        sponda = interpreta_log("Start Movimentazione Sponda alla quota 60.00 mm")
        carro = interpreta_log("Quota Carro 0.04 mm Raggiunta")
        self.assertEqual((sponda.tipo_attivita, sponda.input, sponda.valore), (MOV_X, 1, 60.0))
        self.assertEqual((carro.tipo_attivita, carro.input, carro.valore), (MOV_Y, 0, 0.04))

    def test_arco_negativo_in_gradi(self):
        log = interpreta_log("Feedback Accelerometro Arco -0.05 °")
        self.assertEqual((log.tipo_attivita, log.input, log.valore, log.unita_misura),
                         (MOV_ALPHA, 0, -0.05, "gradi"))

    def test_stati_senza_numero(self):
        self.assertEqual(interpreta_log("Accensione Lama").valore, 1)
        self.assertEqual(interpreta_log("Spegnimento Lama").tipo_attivita, STATO_LAMA)
        self.assertEqual(interpreta_log("Feedback Movimentazione Carro Disattivo").valore, 0)
        self.assertEqual(interpreta_log("Feedback Movimentazione Carro Attivo").input, 0)
        self.assertEqual(interpreta_log("Stato Manuale Attivato").valore, -1)


class UtilitaFemaTest(SimpleTestCase):
    def test_id_record_da_note(self):
        self.assertEqual(id_record_da_note("id:254"), 254)
        self.assertEqual(id_record_da_note("ID: 7"), 7)
        self.assertIsNone(id_record_da_note(None))
        self.assertIsNone(id_record_da_note("nota libera"))

    def test_formatta_misura(self):
        self.assertEqual(formatta_misura(430.0), "430")
        self.assertEqual(formatta_misura(22.5), "22.5")


def risposta_vision(*testi, errore=""):
    return SimpleNamespace(
        error=SimpleNamespace(message=errore),
        text_annotations=[SimpleNamespace(description=t, bounding_poly=SimpleNamespace(vertices=[]))
                          for t in testi],
    )


@override_settings(GOOGLE_APPLICATION_CREDENTIALS="credenziali-finte.json")
@mock.patch("struttura.views.service_account.Credentials.from_service_account_file")
@mock.patch("struttura.views.vision.ImageAnnotatorClient")
class EsitoTextDetectionTest(TestCase):
    """Dopo la scansione la pagina di classificazione mostra lo SweetAlert con l'esito."""

    def setUp(self):
        cliente = Cliente.objects.create(ragione_sociale="C", p_iva="12345678901", email="c@example.com",
                                         cf="CCCCCCCCCCCCCCCC", sede_legale="-")
        tipo = TipoMacchina.objects.create(tipomacchina="VTS-A", desctipomacchina="VTS-A")
        macchina = Macchina.objects.create(tipo_macchina=tipo, desctipomacchina="VTS-A", identificativo="201",
                                           descrmacchina="VTS-A", cliente=cliente)
        tipo_man = TipoManutenzione.objects.create(tipomanutenzione="Ordinaria", settore="Meccanico")
        self.lama = Manutenzione.objects.create(componente="Lama", descrizionecomponente="Lama",
                                                tipo_manutenzione=tipo_man, tipo_macchina=tipo)
        self.motore = Manutenzione.objects.create(componente="Motore", descrizionecomponente="Motore",
                                                  tipo_manutenzione=tipo_man, tipo_macchina=tipo)
        SerialeArticolo.objects.create(codice_articolo_fornitore="LAMA-001", manutenzione=self.lama)
        SerialeArticolo.objects.create(codice_articolo_fornitore="MOT-9", manutenzione=self.motore)
        self.assistenza = Assistenza.objects.create(titolo="A", descassistenza="-", macchine=macchina, stato="aperto")
        Classificazione.objects.create(assistenza=self.assistenza, manutenzione=self.lama)
        utente = CustomUser.objects.create_user(username="u", email="u@example.com", password="x")
        self.client.force_login(utente)
        self.url = reverse("struttura:detect_text_view", args=[self.assistenza.id])

    def invia(self):
        foto = SimpleUploadedFile("foto.png", b"png", content_type="image/png")
        risposta = self.client.post(self.url, {"image": foto}, follow=True)
        self.assertEqual(risposta.status_code, 200)
        return risposta.content.decode()

    def test_seriale_validato_chiude_assistenza(self, client_vision, _):
        client_vision.return_value.text_detection.return_value = risposta_vision("LAMA-001", "LAMA-001")
        pagina = self.invia()
        self.assertIn("icon: 'success'", pagina)
        self.assertIn("Seriale validato. Assistenza chiusa.", pagina)
        self.assertEqual(Assistenza.objects.get(pk=self.assistenza.pk).stato, "chiuso")

    def test_seriale_non_previsto(self, client_vision, _):
        client_vision.return_value.text_detection.return_value = risposta_vision("MOT-9")
        pagina = self.invia()
        self.assertIn("icon: 'warning'", pagina)
        self.assertIn("Seriale non previsto per questa assistenza.", pagina)
        self.assertNotIn("MOT", pagina)

    def test_nessun_seriale(self, client_vision, _):
        client_vision.return_value.text_detection.return_value = risposta_vision("ABC 123", "ABC", "123")
        pagina = self.invia()
        self.assertIn("Seriale non riconosciuto.", pagina)
        self.assertNotIn("ABC", pagina)

    def test_nessun_testo(self, client_vision, _):
        client_vision.return_value.text_detection.return_value = risposta_vision()
        self.assertIn("Nessun testo riconosciuto.", self.invia())

    def test_errore_vision(self, client_vision, _):
        client_vision.return_value.text_detection.side_effect = RuntimeError("quota superata")
        with self.assertLogs("struttura.views", level="ERROR") as log:
            pagina = self.invia()
        self.assertIn("icon: 'error'", pagina)
        self.assertIn("Scansione non riuscita.", pagina)
        self.assertNotIn("quota superata", pagina)
        self.assertIn("quota superata", "\n".join(log.output))

    @override_settings(GOOGLE_APPLICATION_CREDENTIALS=None)
    def test_servizio_non_configurato(self, client_vision, _):
        with self.assertLogs("struttura.views", level="ERROR"):
            pagina = self.invia()
        self.assertIn("Scansione non riuscita.", pagina)
        self.assertNotIn("non configurato", pagina)
        client_vision.assert_not_called()
