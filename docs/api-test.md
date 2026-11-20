# API PIA ICS — documentazione dei test

Questo documento descrive come sono state collaudate le API di sola lettura (`/api/v1/`, vedi *API PIA ICS — documentazione tecnica*), che cosa verificano i test e con quale esito.

## 1. Riepilogo

| Livello | Strumento | Test | Esito |
|---|---|---|---|
| Automatici (unit/integrazione) | `python manage.py test api` | 42 | 42 superati, 0 falliti (~9 s) |
| Regressione dell'intero progetto | `python manage.py test` | 63 | 63 superati |
| End-to-end su server reale | `runserver` + `curl` | 10 chiamate | 10 conformi all'atteso |

Il refactoring della logica di tracciabilità (ora condivisa tra pagina web e API) non ha rotto i 21 test preesistenti.

## 2. Ambiente ed esecuzione

- Python 3.11, Django 5.1.2, database SQLite creato e distrutto a ogni esecuzione (nessun dato reale).
- I test sono in `pia_ics/api/tests.py` e usano il client di test di Django: le richieste attraversano URL, middleware, autenticazione e serializzazione come in produzione.

```bash
cd pia_ics
export DJANGO_SECRET_KEY=qualsiasi        # richiesto da settings.py
python manage.py test api                 # solo le API
python manage.py test api -v 2            # elenco dettagliato dei casi
python manage.py test                     # intero progetto
```

### Dati di prova (fixture)

Quattro utenti (amministratore, manutentore, due clienti), due clienti con una macchina ciascuno (tipi macchina diversi), manutenzioni con seriale, due assistenze (una per cliente) con classificazione, due ordini con commessa, un articolo da 1 m³ / 30 kg, lavorazioni, e log macchina (start ciclo + movimenti) distribuiti sulle due macchine. Così ogni test può distinguere ciò che deve essere visibile da ciò che non deve.

## 3. Casi di test

### 3.1 Autenticazione e metodi (8 test)

| Caso | Verifica |
|---|---|
| Senza credenziali | 401 `non_autenticato` con intestazione `WWW-Authenticate: Bearer` |
| Token errato | 401 `token_non_valido` |
| Schema diverso da Bearer (`Basic`) | 401 |
| Token valido | 200; il token in chiaro non compare nell'hash salvato; `ultimo_uso` viene aggiornato |
| Token disattivato / scaduto / utente disattivato | 401 in ciascuno dei tre casi |
| Sessione web | accettata in alternativa al token |
| POST con token | 405 con `Allow: GET, HEAD` |
| POST con sessione (senza CSRF) | 405, non una scrittura né un errore CSRF |

### 3.2 Perimetro dei dati (5 test)

Verificano che un cliente non possa leggere dati di un altro cliente.

| Caso | Verifica |
|---|---|
| Amministratore e manutentore | vedono tutte le macchine; `accesso_completo = true` |
| Cliente A | vede solo le proprie macchine e anagrafica; macchina e cliente di B danno 404 |
| Cliente A, dati collegati | assistenze, chat, ordini, commesse, lavorazioni, tipi macchina, manutenzioni e log limitati ai propri; assistenza/ordine/ciclo/articolo di B danno 404 |
| Cliente senza clienti associati | 0 macchine e 0 log |
| Tracciabilità | il codice QR di una commessa altrui dà 404, il proprio 200 |

Altri due casi (§3.5) controllano che i filtri non aggirino il perimetro.

### 3.3 Liste, filtri, paginazione (12 test)

| Caso | Verifica |
|---|---|
| Paginazione | `count`, `page`, `page_size`, `num_pages`, ultima pagina parziale, pagina oltre il fondo = lista vuota |
| Parametri non validi | `page_size` 0 e 99999, `page` non numerica o 0, data non valida, `ordinamento` non consentito, id non numerico: sempre 400 `parametro_non_valido` |
| Log: filtri | per macchina, tipo attività, `da` con ora, `a` con sola data (intera giornata), intervallo vuoto, ricerca `q` |
| Log: ordinamento e campi | ordine decrescente; campi e formato ISO 8601 del timestamp |
| Macchine | filtro per cliente, ricerca `q`, struttura annidata di tipo e cliente |
| Sotto-risorse macchina | manutenzioni con seriali, assistenze, documenti |
| Assistenze | filtro per stato e data, fascia oraria e stato leggibile, classificazioni nel dettaglio, 400 su data non valida |
| Calendario | solo occupazione per giorno e 6 fasce; nessun titolo di assistenza esposto |
| Ordine, commessa, articolo | commesse e articoli nel dettaglio ordine, nome cliente ripulito, filtro per `id_record`, volume e densità calcolati (1 m³ → 30 kg/m³) |
| Lavorazioni e attività | filtro per macchina; elenco tipi attività |
| Ciclo ordine | start del ciclo, log della finestra, quote Sponda estratte, macchina |
| Indice e `me` | elenco endpoint, ruolo e clienti dell'utente |

### 3.4 Tracciabilità e qualità (4 test)

| Caso | Verifica |
|---|---|
| Parametri | `qr_data` mancante → 400; codice inesistente → 404 |
| Soglie non configurate | 200 con `qualita_valutata = false` e scarti `null` |
| Qualità calcolata | con soglie e una sequenza reale di movimenti (Arco, Sponda, Carro) l'esito è uno di Ottimo/Rettificare/Scartare, coincide con `controllo_qualita.esito` e gli scarti sono valorizzati |
| `qualita/soglie` | `null` se non configurate, valori se presenti |

### 3.5 Casi aggiuntivi (9 test)

| Caso | Verifica |
|---|---|
| HEAD | consentito (200) |
| PUT / PATCH / DELETE / POST | tutti 405 |
| Chat | ordine cronologico, URL assoluto dell'allegato, `null` se assente, visibile solo al cliente proprietario |
| Documenti | URL assoluto del file; il cliente vede solo i documenti del proprio tipo macchina |
| Formati QR | `262/1`, `IdRecord:262/1`, `id:262/1` e con spazi danno la stessa risposta; senza pezzo `pezzo = null` |
| Numero di query | su log, macchine, assistenze, commesse e lavorazioni le query non crescono con le righe restituite (nessun N+1) |
| Filtri e perimetro | un cliente che filtra per macchina o cliente altrui ottiene 0 risultati |
| Date senza fuso | `2026-04-01T08:01:00` e con spazio sono interpretate in UTC |
| Caratteri accentati | UTF-8 non escapato nel JSON e `Content-Type: application/json` |

### 3.6 Dettagli delle singole risorse (2 test)

Cliente, tipo macchina, manutenzione (con seriali), commessa e articolo: 200 per amministratore e cliente proprietario, 404 per id inesistente; elenco clienti con ricerca `q`.

### 3.7 Comando `crea_token_api` (2 test)

Creazione del token da riga di comando (utente, nome, scadenza a 30 giorni, hash corretto, token realmente utilizzabile) e errore per email inesistente.

## 4. Test end-to-end su server reale

Server avviato con `runserver` su database SQLite temporaneo, utente amministratore e token creato con `crea_token_api`; chiamate eseguite con `curl`.

| Richiesta | Atteso | Ottenuto |
|---|---|---|
| `GET /api/v1/me` senza token | 401 | 401 `application/json` |
| `GET /api/v1/me` token errato | 401 | 401 |
| `GET /api/v1/me` token valido | 200 | 200 |
| `GET /api/v1/macchine` | 200 | 200 |
| `GET /api/v1/macchine/999` | 404 | 404 |
| `GET /api/v1/log?page_size=0` | 400 | 400 |
| `POST /api/v1/macchine` | 405 | 405 |
| `GET /api/v1/tracciabilita?qr_data=262/1` | 200 | 200, JSON con `qualita_valutata: false` (nessun log nei dati di prova) |
| `GET /api/v1/tracciabilita` senza `qr_data` | 400 | 400 |
| `HEAD /api/v1/clienti` | 200 | 200 |

## 5. Difetti trovati durante i test

| Problema | Esito |
|---|---|
| `page_size=0` veniva scambiato per "non indicato" e restituiva 200 con il valore di default | Corretto: ora 400 |
| Il confronto del numero di query risultava diverso per un solo UPDATE di `ultimo_uso` al primo uso del token | Non è un N+1; il test esclude il primo uso |

## 6. Limiti e non coperto

- **Dati reali e volumi**: i test usano pochi record. Non sono stati eseguiti test di carico né di prestazioni sulla tabella `log` di produzione (la più grande): prima del rilascio provare una pagina da 500 righe con filtri `macchina` e `da`/`a` su una copia del DB `PIA_FEMA`.
- **Database**: i test girano su SQLite; in produzione è usato MySQL. Le query sono standard dell'ORM, ma non sono state eseguite su MySQL.
- **Copertura del codice**: non è stato misurato con uno strumento (non installato); la copertura funzionale è quella delle tabelle sopra: ogni endpoint è chiamato almeno una volta.
- **Qualità**: l'algoritmo di controllo qualità è verificato nel suo collegamento alle API, non ricalcolato in modo indipendente; i suoi test specifici restano in `tracciamento/tests.py`.
- **Sicurezza**: non è stato fatto un penetration test. Rate limiting e HTTPS dipendono dall'infrastruttura (vedi la documentazione tecnica, §7).
- **File `/media/`**: non protetti dal token (vedi documentazione tecnica, §2).
