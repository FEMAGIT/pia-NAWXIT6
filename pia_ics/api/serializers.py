"""Rappresentazione JSON delle entità. Ogni funzione riceve (request, oggetto) e restituisce un dict."""

from tracciamento.views import nome_cliente


def _numero(valore):
    return None if valore is None else float(valore)


def _iso(valore):
    return valore.isoformat() if valore else None


def _file(request, campo):
    """URL assoluto di un file caricato (None se assente)."""
    return request.build_absolute_uri(campo.url) if campo else None


def cliente(request, c):
    return {'id': c.id, 'ragione_sociale': c.ragione_sociale, 'p_iva': c.p_iva, 'email': c.email, 'cf': c.cf,
            'sede_legale': c.sede_legale, 'n_telefono': c.n_telefono}


def tipo_macchina(request, t):
    return {'id': t.id, 'codice': t.tipomacchina, 'descrizione': t.desctipomacchina}


def macchina(request, m):
    return {
        'id': m.id,
        'identificativo': m.identificativo,
        'descrizione': m.descrmacchina,
        'tipo_macchina': tipo_macchina(request, m.tipo_macchina),
        'cliente': {'id': m.cliente_id, 'ragione_sociale': m.cliente.ragione_sociale},
    }


def seriale(request, s):
    return {'id': s.id, 'codice_interno': s.codice_interno, 'nome_fornitore': s.nome_fornitore,
            'codice_articolo_fornitore': s.codice_articolo_fornitore,
            'descrizione_articolo_fornitore': s.descrizione_articolo_fornitore}


def manutenzione(request, m, con_seriali=False):
    dati = {
        'id': m.id,
        'componente': m.componente,
        'descrizione': m.descrizionecomponente,
        'link': m.link or None,
        'tipo_manutenzione': {'codice': m.tipo_manutenzione_id, 'settore': m.tipo_manutenzione.settore},
        'tipo_macchina_id': m.tipo_macchina_id,
    }
    if con_seriali:
        dati['seriali'] = [seriale(request, s) for s in m.seriali.all()]
    return dati


def manutenzione_dettaglio(request, m):
    return manutenzione(request, m, con_seriali=True)


def documento(request, d):
    return {'id': d.id, 'nome': d.nome_documento, 'file': _file(request, d.path_documento),
            'tipo_macchina_id': d.tipo_macchina_id}


def assistenza(request, a):
    return {
        'id': a.id,
        'titolo': a.titolo,
        'descrizione': a.descassistenza,
        'data': _iso(a.data),
        'fascia_oraria': a.ora_inizio.strftime('%H:%M') if a.ora_inizio else None,
        'stato': a.stato,
        'stato_descrizione': a.get_stato_display() if a.stato else None,
        'macchina': {'id': a.macchine_id, 'identificativo': a.macchine.identificativo},
    }


def classificazione(request, c):
    return {'id': c.id, 'timestamp': _iso(c.timestamp), 'validata': c.validate,
            'manutenzione': manutenzione(request, c.manutenzione)}


def assistenza_dettaglio(request, a, classificazioni):
    dati = assistenza(request, a)
    dati['classificazioni'] = [classificazione(request, c) for c in classificazioni]
    return dati


def messaggio_chat(request, m):
    return {'id': m.id, 'messaggio': m.messaggio, 'utente': m.utentecorrente, 'data': _iso(m.datacorrente),
            'is_staff': m.is_staff, 'allegato': _file(request, m.preventivo)}


def ordine(request, o):
    return {
        'id': o.id,
        'descrizione': o.descordine,
        'data_consegna': _iso(o.dataconsegna),
        'materiale': o.materiale,
        'id_ordine_esterno': o.id_ordine_esterno,
        'data_inizio': _iso(o.data_inizio),
        'data_fine': _iso(o.data_fine),
    }


def commessa(request, c):
    return {
        'id': c.id,
        'ordine_id': c.ordine_id,
        'id_macchina': c.id_macchina,
        'codice_commessa': c.codicecommessa,
        'descrizione': c.descrizione,
        'id_record': c.id_record,
        'cliente': c.cliente,
        'cliente_nome': nome_cliente(c.cliente),
        'modello': c.modello,
        'componente': c.componente,
        'descrizione_componente': c.desccomponente,
        'dima': c.dima,
        'profondita': c.profondità,
        'quantita_lavorata': c.qtalav,
        'quantita': c.qta,
        'icona': _file(request, c.icona),
    }


def articolo(request, a):
    return {
        'id': a.id,
        'id_esterno': a.id_esterno,
        'tipo': a.tipo,
        'codice': a.codice,
        'altezza_mm': _numero(a.altezza),
        'larghezza_mm': _numero(a.larghezza),
        'spessore_mm': _numero(a.spessore),
        'peso_kg': _numero(a.peso),
        'data_creazione': _iso(a.data_creazione),
    }


def articolo_con_densita(request, a):
    """Articolo con volume (m³) e densità (kg/m³), come mostrato nel report di tracciabilità."""
    dati = articolo(request, a)
    volume = float(a.altezza * a.larghezza * a.spessore) / 1e9
    dati['volume_m3'] = volume
    dati['densita_kg_m3'] = float(a.peso) / volume if volume > 0 else 0
    return dati


def ordine_dettaglio(request, o, commesse, articoli):
    dati = ordine(request, o)
    dati['commesse'] = [commessa(request, c) for c in commesse]
    dati['articoli'] = [articolo(request, a) for a in articoli]
    return dati


def lavorazione(request, l):
    return {'id': l.id, 'id_esterno': l.id_esterno, 'timestamp': _iso(l.timestamp), 'macchina_id': l.macchina_id,
            'commessa_id': l.commessa_id}


def attivita(request, a):
    return {'id': a.id, 'tipo': a.tipo_attività}


def log(request, l):
    return {
        'id': l.id,
        'id_esterno': l.id_esterno,
        'macchina_id': l.macchine_id,
        'tipo_attivita': l.attività.tipo_attività,
        'timestamp': _iso(l.timestamp),
        'descrizione': l.descrizione,
        'input': l.input,
        'output': l.output,
        'valore': l.valore,
        'lunghezza': l.lunghezza,
        'larghezza': l.larghezza,
        'unita_misura': l.unita_misura,
    }
