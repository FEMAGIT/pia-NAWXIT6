"""Infrastruttura comune delle API: autenticazione, errori, paginazione, filtri e perimetro dei dati."""

import functools
from datetime import datetime, time, timedelta, timezone as dt_timezone

from django.core.paginator import EmptyPage, Paginator
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

from autenticazione.models import ApiToken, Cliente
from struttura.models import (Articolo, Assistenza, Chat, Classificazione, Commessa, Documento, Lavorazione, Log,
                              Macchina, Manutenzione, Ordine, SerialeArticolo, TipoMacchina)

PAGE_SIZE_DEFAULT = 100
PAGE_SIZE_MAX = 500
AGGIORNA_ULTIMO_USO_OGNI = timedelta(minutes=1)


class ApiError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status, self.code, self.message = status, code, message


def errore(status, code, message, headers=None):
    risposta = JsonResponse({'error': {'code': code, 'message': message}}, status=status,
                            json_dumps_params={'ensure_ascii': False})
    for chiave, valore in (headers or {}).items():
        risposta[chiave] = valore
    return risposta


def json_response(dati):
    return JsonResponse(dati, json_dumps_params={'ensure_ascii': False})


# ----------------------------------------------------------------------------- autenticazione

def autentica(request):
    """Utente dal token `Authorization: Bearer <token>` oppure, in mancanza, dalla sessione web."""
    intestazione = request.headers.get('Authorization', '')
    if intestazione:
        schema, _, chiave = intestazione.partition(' ')
        if schema.lower() != 'bearer' or not chiave.strip():
            raise ApiError(401, 'non_autenticato', "Intestazione Authorization non valida: usare 'Bearer <token>'.")
        token = (ApiToken.objects.select_related('user')
                 .filter(key_hash=ApiToken.calcola_hash(chiave.strip())).first())
        if token is None or not token.valido:
            raise ApiError(401, 'token_non_valido', "Token inesistente, disattivato o scaduto.")
        adesso = timezone.now()
        if token.ultimo_uso is None or adesso - token.ultimo_uso > AGGIORNA_ULTIMO_USO_OGNI:
            ApiToken.objects.filter(pk=token.pk).update(ultimo_uso=adesso)
        return token.user
    if request.user.is_authenticated:
        return request.user
    raise ApiError(401, 'non_autenticato', "Autenticazione richiesta: inviare 'Authorization: Bearer <token>'.")


def api_view(funzione):
    """Vista di sola lettura: autentica, limita i metodi a GET/HEAD e converte ApiError in JSON."""

    @functools.wraps(funzione)
    def wrapper(request, *args, **kwargs):
        try:
            if request.method not in ('GET', 'HEAD'):
                raise ApiError(405, 'metodo_non_consentito', "Le API sono di sola lettura (GET).")
            utente = autentica(request)
            request.ambito = Ambito(utente)
            return json_response(funzione(request, *args, **kwargs))
        except ApiError as e:
            intestazioni = {'WWW-Authenticate': 'Bearer'} if e.status == 401 else {}
            if e.status == 405:
                intestazioni['Allow'] = 'GET, HEAD'
            return errore(e.status, e.code, e.message, intestazioni)

    wrapper.csrf_exempt = True
    return wrapper


# ----------------------------------------------------------------------------- perimetro dati

class Ambito:
    """Dati visibili all'utente: amministratori e manutentori vedono tutto, i clienti solo i dati
    delle macchine dei clienti a cui sono associati (stessa regola dell'applicazione web)."""

    def __init__(self, user):
        self.user = user
        self.tutto = user.is_superuser or user.role == 'maintenance_worker'
        self.clienti_ids = None if self.tutto else list(user.clienti_associati.values_list('id', flat=True))

    def clienti(self):
        return Cliente.objects.all() if self.tutto else Cliente.objects.filter(id__in=self.clienti_ids)

    def macchine(self):
        qs = Macchina.objects.select_related('tipo_macchina', 'cliente')
        return qs if self.tutto else qs.filter(cliente_id__in=self.clienti_ids)

    def tipi_macchina(self):
        if self.tutto:
            return TipoMacchina.objects.all()
        return TipoMacchina.objects.filter(macchina__cliente_id__in=self.clienti_ids).distinct()

    def manutenzioni(self):
        qs = Manutenzione.objects.select_related('tipo_manutenzione')
        return qs if self.tutto else qs.filter(tipo_macchina__in=self.tipi_macchina())

    def seriali(self):
        qs = SerialeArticolo.objects.all()
        return qs if self.tutto else qs.filter(manutenzione__in=self.manutenzioni())

    def documenti(self):
        qs = Documento.objects.all()
        return qs if self.tutto else qs.filter(tipo_macchina__in=self.tipi_macchina())

    def assistenze(self):
        qs = Assistenza.objects.select_related('macchine')
        return qs if self.tutto else qs.filter(macchine__cliente_id__in=self.clienti_ids)

    def classificazioni(self):
        qs = Classificazione.objects.select_related('manutenzione__tipo_manutenzione')
        return qs if self.tutto else qs.filter(assistenza__in=self.assistenze())

    def chat(self):
        qs = Chat.objects.all()
        return qs if self.tutto else qs.filter(assistenze__in=self.assistenze())

    def commesse(self):
        qs = Commessa.objects.all()
        if self.tutto:
            return qs
        return qs.filter(id_macchina__in=self.macchine().values('identificativo'))

    def ordini(self):
        if self.tutto:
            return Ordine.objects.all()
        return Ordine.objects.filter(id__in=self.commesse().values('ordine_id'))

    def articoli(self):
        if self.tutto:
            return Articolo.objects.all()
        return Articolo.objects.filter(ordine__in=self.ordini()).distinct()

    def lavorazioni(self):
        qs = Lavorazione.objects.select_related('macchina', 'commessa')
        return qs if self.tutto else qs.filter(macchina__in=self.macchine())

    def log(self):
        qs = Log.objects.select_related('attività')
        return qs if self.tutto else qs.filter(macchine__in=self.macchine())


def oggetto(qs, **filtri):
    """Primo oggetto del queryset (già limitato al perimetro dell'utente) o 404."""
    trovato = qs.filter(**filtri).first()
    if trovato is None:
        raise ApiError(404, 'non_trovato', "Risorsa inesistente o non accessibile.")
    return trovato


# ----------------------------------------------------------------------------- parametri

def param_int(request, nome):
    valore = request.GET.get(nome)
    if valore in (None, ''):
        return None
    try:
        return int(valore)
    except ValueError:
        raise ApiError(400, 'parametro_non_valido', f"Il parametro '{nome}' deve essere un numero intero.")


def param_testo(request, nome):
    valore = request.GET.get(nome)
    return valore.strip() if valore and valore.strip() else None


def _data_ora(valore, nome):
    """(datetime consapevole, True se era una sola data). Le date/ore senza fuso sono in UTC."""
    try:
        solo_data = parse_date(valore) if 'T' not in valore and ' ' not in valore else None
        quando = parse_datetime(valore)
    except ValueError:
        solo_data = quando = None
    if solo_data is not None:
        quando = datetime.combine(solo_data, time.min)
    elif quando is None:
        raise ApiError(400, 'parametro_non_valido',
                       f"Il parametro '{nome}' deve essere una data (AAAA-MM-GG) o data e ora ISO 8601.")
    if timezone.is_naive(quando):
        quando = quando.replace(tzinfo=dt_timezone.utc)
    return quando, solo_data is not None


def filtra_periodo(request, qs, campo):
    """Filtra un campo data/ora tra ?da= (incluso) e ?a= (incluso; con sola data comprende tutta la giornata)."""
    valore_da, valore_a = param_testo(request, 'da'), param_testo(request, 'a')
    if valore_da:
        qs = qs.filter(**{f'{campo}__gte': _data_ora(valore_da, 'da')[0]})
    if valore_a:
        fine, solo_data = _data_ora(valore_a, 'a')
        qs = qs.filter(**({f'{campo}__lt': fine + timedelta(days=1)} if solo_data else {f'{campo}__lte': fine}))
    return qs


def filtra_periodo_data(request, qs, campo):
    """Come filtra_periodo per un campo DateField (solo date)."""
    for nome, confronto in (('da', 'gte'), ('a', 'lte')):
        valore = param_testo(request, nome)
        if valore:
            try:
                data = parse_date(valore)
            except ValueError:
                data = None
            if data is None:
                raise ApiError(400, 'parametro_non_valido', f"Il parametro '{nome}' deve essere una data AAAA-MM-GG.")
            qs = qs.filter(**{f'{campo}__{confronto}': data})
    return qs


def ordina(request, qs, consentiti, predefinito):
    """?ordinamento=campo o -campo, limitato ai campi dichiarati."""
    richiesto = param_testo(request, 'ordinamento')
    if richiesto is None:
        return qs.order_by(*predefinito)
    if richiesto.lstrip('-') not in consentiti:
        raise ApiError(400, 'parametro_non_valido',
                       f"Ordinamento non supportato; campi consentiti: {', '.join(sorted(consentiti))}.")
    return qs.order_by(richiesto, 'pk')


# ----------------------------------------------------------------------------- paginazione

def pagina(request, qs, serializza):
    dimensione, numero = param_int(request, 'page_size'), param_int(request, 'page')
    dimensione = PAGE_SIZE_DEFAULT if dimensione is None else dimensione
    numero = 1 if numero is None else numero
    if not 1 <= dimensione <= PAGE_SIZE_MAX:
        raise ApiError(400, 'parametro_non_valido', f"'page_size' deve essere tra 1 e {PAGE_SIZE_MAX}.")
    if numero < 1:
        raise ApiError(400, 'parametro_non_valido', "'page' deve essere almeno 1.")
    paginatore = Paginator(qs, dimensione)
    try:
        elementi = list(paginatore.page(numero).object_list)
    except EmptyPage:
        elementi = []
    return {
        'count': paginatore.count,
        'page': numero,
        'page_size': dimensione,
        'num_pages': paginatore.num_pages,
        'results': [serializza(e) for e in elementi],
    }
