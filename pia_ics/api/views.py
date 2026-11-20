"""Endpoint delle API (sola lettura). Documentazione: docs/api.md."""

from collections import defaultdict

from django.db.models import Q
from django.urls import reverse

from struttura.models import (Attività, FASCE_ORARIE_ASSISTENZA, Assistenza, QualitàAngoloAutomatico, QualitàTaglio)
from tracciamento.views import analizza_tracciabilita, estrai_movimenti, log_ciclo_ordine

from . import serializers as ser
from .core import (ApiError, api_view, filtra_periodo, filtra_periodo_data, oggetto, ordina, pagina, param_int,
                   param_testo)

ESITI_QUALITÀ = ('Ottimo', 'Rettificare', 'Scartare')


def _filtro_id(request, qs, nome, campo):
    valore = param_int(request, nome)
    return qs if valore is None else qs.filter(**{campo: valore})


def _ricerca(request, qs, *campi):
    q = param_testo(request, 'q')
    if not q:
        return qs
    condizione = Q()
    for campo in campi:
        condizione |= Q(**{f'{campo}__icontains': q})
    return qs.filter(condizione)


def _lista(request, qs, serializzatore):
    return pagina(request, qs, lambda o: serializzatore(request, o))


# ----------------------------------------------------------------------------- generale

ENDPOINT = [
    ('me', 'Utente autenticato e clienti associati'),
    ('clienti', 'Clienti'),
    ('macchine', 'Macchine (filtri: cliente, tipo_macchina, q)'),
    ('tipi-macchina', 'Tipi di macchina'),
    ('manutenzioni', 'Manutenzioni e seriali (filtri: tipo_macchina, tipo_manutenzione, q)'),
    ('documenti', 'Documenti dei tipi macchina (filtro: tipo_macchina)'),
    ('assistenze', 'Assistenze (filtri: macchina, cliente, stato, da, a, q)'),
    ('calendario', 'Fasce orarie e occupazione giornaliera'),
    ('ordini', 'Ordini di produzione (filtri: da, a, q)'),
    ('commesse', 'Commesse (filtri: ordine, id_record, id_macchina, q)'),
    ('articoli', 'Articoli/blocchi (filtri: ordine, da, a, q)'),
    ('lavorazioni', 'Lavorazioni (filtri: macchina, commessa, da, a)'),
    ('attivita', 'Tipi di attività dei log macchina'),
    ('log', 'Log macchina (filtri: macchina, tipo_attivita, da, a, q)'),
    ('tracciabilita', 'Tracciabilità e controllo qualità da QR code (?qr_data=)'),
    ('qualita/soglie', 'Soglie del controllo qualità'),
]


@api_view
def indice(request):
    return {
        'nome': 'PIA ICS API',
        'versione': 'v1',
        'endpoint': [{'percorso': reverse('api:indice') + percorso, 'descrizione': descrizione}
                     for percorso, descrizione in ENDPOINT],
    }


@api_view
def me(request):
    utente = request.ambito.user
    return {
        'id': utente.id,
        'email': utente.email,
        'username': utente.username,
        'nome': utente.get_full_name(),
        'ruolo': utente.role,
        'amministratore': utente.is_superuser,
        'accesso_completo': request.ambito.tutto,
        'clienti': [ser.cliente(request, c) for c in utente.clienti_associati.order_by('ragione_sociale')],
    }


# ----------------------------------------------------------------------------- clienti e macchine

@api_view
def clienti(request):
    qs = _ricerca(request, request.ambito.clienti(), 'ragione_sociale', 'p_iva', 'email')
    return _lista(request, qs.order_by('ragione_sociale', 'pk'), ser.cliente)


@api_view
def cliente_dettaglio(request, pk):
    return ser.cliente(request, oggetto(request.ambito.clienti(), pk=pk))


@api_view
def macchine(request):
    qs = request.ambito.macchine()
    qs = _filtro_id(request, qs, 'cliente', 'cliente_id')
    qs = _filtro_id(request, qs, 'tipo_macchina', 'tipo_macchina_id')
    qs = _ricerca(request, qs, 'identificativo', 'descrmacchina', 'cliente__ragione_sociale')
    qs = ordina(request, qs, {'id', 'identificativo'}, ['identificativo', 'pk'])
    return _lista(request, qs, ser.macchina)


@api_view
def macchina_dettaglio(request, pk):
    return ser.macchina(request, oggetto(request.ambito.macchine(), pk=pk))


@api_view
def macchina_manutenzioni(request, pk):
    m = oggetto(request.ambito.macchine(), pk=pk)
    qs = request.ambito.manutenzioni().filter(tipo_macchina_id=m.tipo_macchina_id).prefetch_related('seriali')
    return _lista(request, qs.order_by('componente', 'pk'), ser.manutenzione_dettaglio)


@api_view
def macchina_documenti(request, pk):
    m = oggetto(request.ambito.macchine(), pk=pk)
    qs = request.ambito.documenti().filter(tipo_macchina_id=m.tipo_macchina_id)
    return _lista(request, qs.order_by('nome_documento', 'pk'), ser.documento)


@api_view
def macchina_assistenze(request, pk):
    m = oggetto(request.ambito.macchine(), pk=pk)
    qs = request.ambito.assistenze().filter(macchine=m)
    return _lista(request, qs.order_by('-data', '-pk'), ser.assistenza)


@api_view
def tipi_macchina(request):
    qs = _ricerca(request, request.ambito.tipi_macchina(), 'tipomacchina', 'desctipomacchina')
    return _lista(request, qs.order_by('tipomacchina', 'pk'), ser.tipo_macchina)


@api_view
def tipo_macchina_dettaglio(request, pk):
    return ser.tipo_macchina(request, oggetto(request.ambito.tipi_macchina(), pk=pk))


# ----------------------------------------------------------------------------- manutenzioni e documenti

@api_view
def manutenzioni(request):
    qs = request.ambito.manutenzioni().prefetch_related('seriali')
    qs = _filtro_id(request, qs, 'tipo_macchina', 'tipo_macchina_id')
    tipo = param_testo(request, 'tipo_manutenzione')
    if tipo:
        qs = qs.filter(tipo_manutenzione_id=tipo)
    qs = _ricerca(request, qs, 'componente', 'descrizionecomponente')
    return _lista(request, qs.order_by('componente', 'pk'), ser.manutenzione_dettaglio)


@api_view
def manutenzione_dettaglio(request, pk):
    qs = request.ambito.manutenzioni().prefetch_related('seriali')
    return ser.manutenzione_dettaglio(request, oggetto(qs, pk=pk))


@api_view
def documenti(request):
    qs = _filtro_id(request, request.ambito.documenti(), 'tipo_macchina', 'tipo_macchina_id')
    qs = _ricerca(request, qs, 'nome_documento')
    return _lista(request, qs.order_by('nome_documento', 'pk'), ser.documento)


# ----------------------------------------------------------------------------- assistenze

@api_view
def assistenze(request):
    qs = request.ambito.assistenze()
    qs = _filtro_id(request, qs, 'macchina', 'macchine_id')
    qs = _filtro_id(request, qs, 'cliente', 'macchine__cliente_id')
    stato = param_testo(request, 'stato')
    if stato:
        qs = qs.filter(stato=stato)
    qs = filtra_periodo_data(request, qs, 'data')
    qs = _ricerca(request, qs, 'titolo', 'descassistenza')
    qs = ordina(request, qs, {'id', 'data'}, ['-data', '-pk'])
    return _lista(request, qs, ser.assistenza)


@api_view
def assistenza_dettaglio(request, pk):
    a = oggetto(request.ambito.assistenze(), pk=pk)
    classificazioni = request.ambito.classificazioni().filter(assistenza=a).order_by('timestamp', 'pk')
    return ser.assistenza_dettaglio(request, a, classificazioni)


@api_view
def assistenza_chat(request, pk):
    a = oggetto(request.ambito.assistenze(), pk=pk)
    qs = request.ambito.chat().filter(assistenze=a).order_by('datacorrente', 'pk')
    return _lista(request, qs, ser.messaggio_chat)


@api_view
def calendario(request):
    """Come la vista web: solo occupazione delle fasce, senza titoli né descrizioni delle assistenze."""
    occupati = defaultdict(list)
    prenotazioni = Assistenza.objects.filter(data__isnull=False, ora_inizio__isnull=False)
    prenotazioni = filtra_periodo_data(request, prenotazioni, 'data')
    for data, ora in prenotazioni.values_list('data', 'ora_inizio').order_by('data', 'ora_inizio'):
        occupati[data.isoformat()].append(ora.strftime('%H:%M'))
    fasce = [{'inizio': inizio.strftime('%H:%M'), 'fine': f'{inizio.hour + 1:02d}:00', 'etichetta': etichetta}
             for inizio, etichetta in FASCE_ORARIE_ASSISTENZA]
    return {'fasce': fasce, 'occupati_per_giorno': occupati}


# ----------------------------------------------------------------------------- produzione

@api_view
def ordini(request):
    qs = filtra_periodo_data(request, request.ambito.ordini(), 'dataconsegna')
    qs = _ricerca(request, qs, 'descordine', 'materiale', 'id_ordine_esterno')
    qs = ordina(request, qs, {'id', 'dataconsegna', 'id_ordine_esterno'}, ['-dataconsegna', '-pk'])
    return _lista(request, qs, ser.ordine)


@api_view
def ordine_dettaglio(request, pk):
    o = oggetto(request.ambito.ordini(), pk=pk)
    commesse = request.ambito.commesse().filter(ordine=o).order_by('pk')
    articoli = request.ambito.articoli().filter(ordine=o).order_by('pk')
    return ser.ordine_dettaglio(request, o, commesse, articoli)


@api_view
def ordine_ciclo(request, pk):
    """Log del ciclo automatico dell'ordine e movimenti estratti (quote Sponda/Carro, angoli dell'Arco)."""
    o = oggetto(request.ambito.ordini(), pk=pk)
    prima = request.ambito.commesse().filter(ordine=o).order_by('pk').first()
    macchina = (request.ambito.macchine().filter(identificativo=prima.id_macchina).first() if prima else None)
    if macchina is None and not request.ambito.tutto:
        start, logs = None, []
    else:
        start, logs = log_ciclo_ordine(o, macchina)
    quote_x, quote_y, angoli = estrai_movimenti(logs)
    return {
        'ordine_id': o.id,
        'macchina_id': macchina.id if macchina else None,
        'start': ser.log(request, start) if start else None,
        'log': [ser.log(request, l) for l in logs],
        'movimenti': {
            'quote_sponda_x': quote_x,
            'quote_carro_y': quote_y,
            'angoli_arco': [{'prima': prima_, 'dopo': dopo} for prima_, dopo in angoli],
        },
    }


@api_view
def commesse(request):
    qs = request.ambito.commesse()
    qs = _filtro_id(request, qs, 'ordine', 'ordine_id')
    for nome, campo in (('id_record', 'id_record'), ('id_macchina', 'id_macchina')):
        valore = param_testo(request, nome)
        if valore:
            qs = qs.filter(**{campo: valore})
    qs = _ricerca(request, qs, 'codicecommessa', 'descrizione', 'modello', 'componente', 'cliente')
    return _lista(request, qs.order_by('pk'), ser.commessa)


@api_view
def commessa_dettaglio(request, pk):
    return ser.commessa(request, oggetto(request.ambito.commesse(), pk=pk))


@api_view
def articoli(request):
    qs = _filtro_id(request, request.ambito.articoli(), 'ordine', 'ordine')
    qs = filtra_periodo(request, qs, 'data_creazione')
    qs = _ricerca(request, qs, 'codice')
    return _lista(request, qs.order_by('pk'), ser.articolo_con_densita)


@api_view
def articolo_dettaglio(request, pk):
    return ser.articolo_con_densita(request, oggetto(request.ambito.articoli(), pk=pk))


@api_view
def lavorazioni(request):
    qs = request.ambito.lavorazioni()
    qs = _filtro_id(request, qs, 'macchina', 'macchina_id')
    qs = _filtro_id(request, qs, 'commessa', 'commessa_id')
    qs = filtra_periodo(request, qs, 'timestamp')
    qs = ordina(request, qs, {'id', 'timestamp'}, ['timestamp', 'pk'])
    return _lista(request, qs, ser.lavorazione)


@api_view
def attivita(request):
    return _lista(request, Attività.objects.order_by('tipo_attività', 'pk'), ser.attivita)


@api_view
def log(request):
    qs = request.ambito.log()
    qs = _filtro_id(request, qs, 'macchina', 'macchine_id')
    tipo = param_testo(request, 'tipo_attivita')
    if tipo:
        qs = qs.filter(attività__tipo_attività=tipo)
    qs = filtra_periodo(request, qs, 'timestamp')
    qs = _ricerca(request, qs, 'descrizione')
    qs = ordina(request, qs, {'id', 'timestamp'}, ['timestamp', 'pk'])
    return _lista(request, qs, ser.log)


# ----------------------------------------------------------------------------- tracciabilità e qualità

def _scarto(valore):
    return valore if isinstance(valore, (int, float)) else None


@api_view
def tracciabilita(request):
    """Equivalente JSON del report di tracciabilità aperto dal QR code (stessi calcoli)."""
    qr_data = param_testo(request, 'qr_data')
    if not qr_data:
        raise ApiError(400, 'parametro_mancante', "Il parametro 'qr_data' è obbligatorio (es. 262/3).")
    contesto = analizza_tracciabilita(qr_data, request.ambito.commesse())
    if contesto is None:
        raise ApiError(404, 'non_trovato', "Nessuna commessa trovata per il codice indicato.")

    articoli_visti, articoli = set(), []
    for o in contesto['ordini']:
        for a in o.articoli.all():
            if a.id not in articoli_visti:
                articoli_visti.add(a.id)
                articoli.append(ser.articolo_con_densita(request, a))

    return {
        'codice': contesto['codice'],
        'pezzo': contesto['pezzo_qr'],
        'cliente': contesto['cliente'],
        'qualita': contesto['qualità'],
        'qualita_valutata': contesto['qualità'] in ESITI_QUALITÀ,
        'scarto_x_mm': _scarto(contesto['scartox']),
        'scarto_y_mm': _scarto(contesto['scartoy']),
        'commesse': [{
            'commessa': ser.commessa(request, d['commessa']),
            'ordine': ser.ordine(request, d['commessa'].ordine),
            'macchina': ser.macchina(request, d['macchina']) if d['macchina'] else None,
            'controllo_qualita': {
                'esito': d['qualità'],
                'valutato': d['qualità'] in ESITI_QUALITÀ,
                'scarto_x_mm': d['scarto_x'],
                'scarto_y_mm': d['scarto_y'],
            },
        } for d in contesto['dettaglio']],
        'articoli': articoli,
    }


@api_view
def soglie_qualita(request):
    angolo = QualitàAngoloAutomatico.objects.first()
    taglio = QualitàTaglio.objects.first()
    return {
        'angolo_automatico': {'soglia_ottimo': angolo.soglia_ottimo, 'soglia_rettifica': angolo.soglia_rettifica}
        if angolo else None,
        'taglio': {'soglia_accettabile': taglio.soglia_accettabile} if taglio else None,
    }
