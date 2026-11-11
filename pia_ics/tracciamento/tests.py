from types import SimpleNamespace

from django.test import SimpleTestCase

from struttura.fema import interpreta_log
from tracciamento.views import distanza_pezzo, estrai_movimenti, leggi_codice_qr, nome_cliente


def log_da_testi(*testi):
    """Simula i Log importati: stessi campi usati da estrai_movimenti."""
    logs = []
    for testo in testi:
        info = interpreta_log(testo)
        logs.append(SimpleNamespace(
            descrizione=testo, input=info.input, valore=info.valore,
            attività=SimpleNamespace(tipo_attività=info.tipo_attivita),
        ))
    return logs


class EstraiMovimentiTest(SimpleTestCase):
    def test_sequenza_reale_ordine_2600028(self):
        logs = log_da_testi(
            "Feedback Accelerometro Arco 0.10 °",
            "Start Movimentazione Sponda alla quota 60.00 mm",
            "Quota Sponda 60.00 mm Raggiunta",
            "Feedback Accelerometro Arco 0.10 °",
            "Start Movimentazione Carro alla quota 2360.00 mm",
            "Feedback Movimentazione Carro Attivo",
            "Quota Carro 0.04 mm Raggiunta",
            "Feedback Movimentazione Carro Disattivo",
            "Feedback Accelerometro Arco 0.11 °",
            "Start Movimentazione Carro alla quota 0.04 mm",
            "Quota Carro 0.04 mm Raggiunta",
            "Feedback Accelerometro Arco 0.12 °",
            "Start Movimentazione Sponda alla quota 45.00 mm",
        )
        quote_x, quote_y, angoli = estrai_movimenti(logs)
        self.assertEqual(quote_x, [60.0, 45.0])
        self.assertEqual(quote_y, [2360.0, 0.04])
        self.assertEqual(angoli, [(0.10, 0.11), (0.11, 0.12)])
        self.assertEqual(distanza_pezzo(quote_x, 0), 15.0)

    def test_senza_accelerometro(self):
        logs = log_da_testi("Start Movimentazione Carro alla quota 2360.00 mm", "Quota Carro 0.00 mm Raggiunta")
        self.assertEqual(estrai_movimenti(logs)[2], [(None, None)])


class UtilitaTracciamentoTest(SimpleTestCase):
    def test_leggi_codice_qr(self):
        self.assertEqual(leggi_codice_qr("IdRecord:254"), "254")
        self.assertEqual(leggi_codice_qr("id:254"), "254")
        self.assertEqual(leggi_codice_qr(" 254 "), "254")
        self.assertEqual(leggi_codice_qr(None), "")

    def test_nome_cliente(self):
        self.assertEqual(nome_cliente("501.00141 GLAMOUR SOFA' S"), "GLAMOUR SOFA' S")
        self.assertEqual(nome_cliente("Nettuno sofa"), "Nettuno sofa")
