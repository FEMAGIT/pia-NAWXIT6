# API PIA ICS — documentazione tecnica

API REST di **sola lettura** che espongono in JSON i dati della piattaforma: clienti, macchine, manutenzioni, assistenze, produzione (ordini, commesse, articoli, lavorazioni), log macchina e report di tracciabilità/qualità.

- Base URL: `https://<host>/api/v1/`
- Formato: JSON UTF-8
- Metodi: solo `GET` (e `HEAD`). Ogni altro metodo risponde `405`.
- Implementazione: app Django `pia_ics/api/` (nessuna dipendenza aggiuntiva).

## 1. Autenticazione

Ogni richiesta richiede un **token** associato a un utente della piattaforma:

```
Authorization: Bearer <token>
```

### Creare un token

Dalla cartella `pia_ics`:

```bash
python manage.py crea_token_api utente@esempio.it --nome "Gestionale ERP" [--giorni 365]
```

Il token in chiaro viene mostrato **una sola volta**; nel database è salvato solo l'hash SHA-256. Dall'admin (`/admin/` → *Token API*) si possono consultare, disattivare o far scadere i token (data `scadenza`). Un token non è più valido se è disattivato, scaduto o se l'utente è disattivato. Si consiglia un utente dedicato per ogni integrazione.

In alternativa al token, le API accettano anche la sessione web già autenticata (utile per provarle dal browser). Essendo di sola lettura non c'è rischio CSRF.

### Perimetro dei dati

| Utente | Dati visibili |
|---|---|
| Superuser, ruolo `maintenance_worker` | Tutti i dati |
| Ruolo `client` (e altri) | Solo i dati delle macchine dei **clienti a cui è associato** (anagrafica cliente, macchine, assistenze, chat, manutenzioni/documenti dei loro tipi macchina, lavorazioni, log, commesse con `id_macchina` di una loro macchina, relativi ordini e articoli) |

Una risorsa fuori perimetro risponde `404` (non `403`), per non rivelarne l'esistenza. Eccezioni: `attivita`, `qualita/soglie` e `calendario` sono dati di riferimento comuni a tutti.

## 2. Convenzioni

### Liste e paginazione

Gli endpoint di elenco restituiscono:

```json
{
  "count": 1240,
  "page": 1,
  "page_size": 100,
  "num_pages": 13,
  "results": [ ... ]
}
```

| Parametro | Default | Note |
|---|---|---|
| `page` | `1` | Una pagina oltre l'ultima restituisce `results` vuoto |
| `page_size` | `100` | Da 1 a 500 |
| `ordinamento` | vedi endpoint | Nome del campo, con `-` davanti per l'ordine decrescente. Solo dove indicato |
| `q` | — | Ricerca testuale (contiene, case-insensitive) sui campi indicati per endpoint |

Per scaricare tutto un elenco (es. `log`) scorrere `page` da 1 a `num_pages`.

### Date e orari

- Timestamp in **ISO 8601 con fuso** (`2026-04-01T08:00:00+00:00`), sempre in **UTC**.
- I filtri `da` / `a` accettano una data (`2026-04-01`) o data e ora (`2026-04-01T08:30:00Z`). Valori senza fuso sono interpretati in UTC. Sono estremi **inclusi**; con `a` in forma di sola data si include l'intera giornata.
- Sugli endpoint con date semplici (`assistenze`, `ordini`, `calendario`) `da`/`a` sono date `AAAA-MM-GG`.

### Errori

Stato HTTP appropriato e corpo uniforme:

```json
{ "error": { "code": "token_non_valido", "message": "Token inesistente, disattivato o scaduto." } }
```

| HTTP | `code` | Causa |
|---|---|---|
| 400 | `parametro_non_valido` | Valore non valido (numero, data, `page_size`, `ordinamento`) |
| 400 | `parametro_mancante` | Parametro obbligatorio assente |
| 401 | `non_autenticato` | Nessuna credenziale o intestazione malformata (risposta con `WWW-Authenticate: Bearer`) |
| 401 | `token_non_valido` | Token inesistente, disattivato, scaduto o utente disattivato |
| 404 | `non_trovato` | Risorsa inesistente o fuori dal perimetro dell'utente |
| 405 | `metodo_non_consentito` | Metodo diverso da GET/HEAD |

### File

I campi `file`, `allegato`, `icona` sono **URL assoluti** (oppure `null`). I file sono serviti da `/media/`: Django lo fa solo con `DJANGO_DEBUG=True`; in produzione `/media/` va servito dal web server (Nginx/Apache) e **non è protetto dal token**.

## 3. Endpoint

Tutti i percorsi sono relativi a `/api/v1/`. `GET /api/v1/` restituisce l'elenco aggiornato degli endpoint.

| Percorso | Descrizione |
|---|---|
| `me` | Utente del token e clienti associati |
| `clienti`, `clienti/{id}` | Clienti. `q`: ragione sociale, P.IVA, email |
| `macchine`, `macchine/{id}` | Macchine. Filtri: `cliente`, `tipo_macchina` (id), `q` (identificativo, descrizione, cliente). `ordinamento`: `id`, `identificativo` |
| `macchine/{id}/manutenzioni` | Manutenzioni del tipo della macchina, con seriali |
| `macchine/{id}/documenti` | Documenti del tipo della macchina |
| `macchine/{id}/assistenze` | Assistenze della macchina |
| `tipi-macchina`, `tipi-macchina/{id}` | Tipi di macchina. `q` |
| `manutenzioni`, `manutenzioni/{id}` | Filtri: `tipo_macchina` (id), `tipo_manutenzione` (codice), `q` |
| `documenti` | Filtri: `tipo_macchina`, `q` |
| `assistenze`, `assistenze/{id}` | Filtri: `macchina`, `cliente`, `stato`, `da`, `a` (data assistenza), `q`. `ordinamento`: `id`, `data` (default `-data`). Il dettaglio include le classificazioni |
| `assistenze/{id}/chat` | Messaggi dell'assistenza in ordine cronologico |
| `calendario` | Fasce orarie prenotabili e occupazione per giorno. Filtri: `da`, `a`. Non espone titoli/descrizioni |
| `ordini`, `ordini/{id}` | Filtri: `da`, `a` (data consegna), `q`. `ordinamento`: `id`, `dataconsegna`, `id_ordine_esterno`. Il dettaglio include commesse e articoli |
| `ordini/{id}/ciclo` | Log del ciclo automatico dell'ordine e movimenti estratti |
| `commesse`, `commesse/{id}` | Filtri: `ordine` (id), `id_record`, `id_macchina` (identificativo), `q` |
| `articoli`, `articoli/{id}` | Blocchi. Filtri: `ordine` (id), `da`, `a` (data creazione), `q` (codice) |
| `lavorazioni` | Filtri: `macchina`, `commessa` (id), `da`, `a`. `ordinamento`: `id`, `timestamp` |
| `attivita` | Tipi di attività dei log |
| `log` | Log macchina. Filtri: `macchina` (id), `tipo_attivita`, `da`, `a`, `q` (descrizione). `ordinamento`: `id`, `timestamp` (default cronologico) |
| `tracciabilita?qr_data=` | Report di tracciabilità e controllo qualità del pezzo |
| `qualita/soglie` | Soglie di configurazione del controllo qualità |

Valori di `stato` delle assistenze: `aperto`, `in_elaborazione`, `sospeso`, `accettazione`, `accettato`, `chiuso`, `chiuso_positivamente`, `chiuso_negativamente`.

Valori di `tipo_attivita` dei log: `Movimentazione x` (Sponda), `Movimentazione y` (Carro), `Movimentazione alpha` (Arco, angolo in gradi), `Stato lama`, `Stato ciclo Automatico`, `Azione`.

## 4. Schemi delle risorse

### Cliente
```json
{ "id": 1, "ragione_sociale": "Alfa Srl", "p_iva": "01234567890", "email": "info@alfa.it",
  "cf": "01234567890", "sede_legale": "Roma", "n_telefono": "0612345678" }
```

### Macchina
```json
{ "id": 4, "identificativo": "M-A", "descrizione": "Macchina Alfa",
  "tipo_macchina": { "id": 2, "codice": "TAGLIO", "descrizione": "Taglio" },
  "cliente": { "id": 1, "ragione_sociale": "Alfa Srl" } }
```

### Manutenzione
```json
{ "id": 9, "componente": "Lama", "descrizione": "Lama circolare", "link": null,
  "tipo_manutenzione": { "codice": "meccanico", "settore": "Meccanica" },
  "tipo_macchina_id": 2,
  "seriali": [ { "id": 1, "codice_interno": "S1", "nome_fornitore": null,
                 "codice_articolo_fornitore": null, "descrizione_articolo_fornitore": null } ] }
```
(`seriali` è presente su `manutenzioni`, `manutenzioni/{id}` e `macchine/{id}/manutenzioni`.)

### Documento
```json
{ "id": 3, "nome": "Manuale", "file": "https://host/media/documenti/manuale.pdf", "tipo_macchina_id": 2 }
```

### Assistenza
```json
{ "id": 12, "titolo": "Guasto lama", "descrizione": "…", "data": "2026-03-10", "fascia_oraria": "09:00",
  "stato": "aperto", "stato_descrizione": "Aperto",
  "macchina": { "id": 4, "identificativo": "M-A" } }
```
Il dettaglio aggiunge `classificazioni`: `[{ "id", "timestamp", "validata", "manutenzione": {…Manutenzione senza seriali…} }]`.

### Messaggio di chat
```json
{ "id": 77, "messaggio": "Preventivo allegato", "utente": "mario", "data": "2026-03-10T09:15:00+00:00",
  "is_staff": true, "allegato": "https://host/media/preventivo.pdf" }
```

### Ordine
```json
{ "id": 5, "descrizione": "Ordine 2600028", "data_consegna": "2026-04-01", "materiale": "PU",
  "id_ordine_esterno": "2600028", "data_inizio": "2026-04-01T08:00:00+00:00", "data_fine": null }
```
Il dettaglio aggiunge `commesse` (lista di Commessa) e `articoli` (lista di Articolo).

### Commessa
```json
{ "id": 21, "ordine_id": 5, "id_macchina": "M-A", "codice_commessa": "C-A", "descrizione": "…",
  "id_record": "262", "cliente": "501.00141 GLAMOUR SOFA' S", "cliente_nome": "GLAMOUR SOFA' S",
  "modello": null, "componente": null, "descrizione_componente": null,
  "dima": "430X60", "profondita": 60.0, "quantita_lavorata": 1, "quantita": 2,
  "icona": "https://host/media/icon/Sagoma_1.png" }
```
`id_macchina` coincide con l'`identificativo` della Macchina. `dima` è "PRIMISxSECMIS" in mm; `profondita` in mm.

### Articolo (blocco)
```json
{ "id": 8, "id_esterno": 1042, "tipo": "BLK", "codice": "ART-A", "altezza_mm": 1000.0, "larghezza_mm": 1000.0,
  "spessore_mm": 1000.0, "peso_kg": 30.0, "data_creazione": "2026-03-01T10:00:00+00:00",
  "volume_m3": 1.0, "densita_kg_m3": 30.0 }
```
`volume_m3` e `densita_kg_m3` sono calcolati come nel report di tracciabilità (sugli endpoint `articoli` e `tracciabilita`; nel dettaglio ordine sono omessi).

### Lavorazione
```json
{ "id": 3, "id_esterno": 90001, "timestamp": "2026-04-01T08:00:00+00:00", "macchina_id": 4, "commessa_id": 21 }
```

### Log macchina
```json
{ "id": 100234, "id_esterno": 5588123, "macchina_id": 4, "tipo_attivita": "Movimentazione x",
  "timestamp": "2026-04-01T08:01:00+00:00", "descrizione": "Start Movimentazione Sponda alla quota 60.00 mm",
  "input": 1, "output": 0, "valore": 60.0, "lunghezza": null, "larghezza": null, "unita_misura": "mm" }
```
`input` = 1 per i comandi, 0 per i feedback. `valore` è il primo numero della descrizione (−1 se assente; 1/0 per stati attivo/disattivo). `lunghezza`/`larghezza` sono valorizzati solo nello start del ciclo automatico.

## 5. Endpoint di produzione e qualità

### `GET ordini/{id}/ciclo`

Restituisce il ciclo automatico dell'ordine (dallo "Start Ciclo Automatico" al primo messaggio di ciclo successivo) e i movimenti estratti.

```json
{
  "ordine_id": 5,
  "macchina_id": 4,
  "start": { "id": 100230, "descrizione": "Start Ciclo Automatico ID_Ordine 2600028 (430.00 x 60.00 mm)", "…": "…" },
  "log": [ { "…": "Log macchina, in ordine cronologico" } ],
  "movimenti": {
    "quote_sponda_x": [60.0],
    "quote_carro_y": [0.0, 430.0],
    "angoli_arco": [ { "prima": 0.1, "dopo": 0.1 } ]
  }
}
```
`start` è `null` e `log` vuoto se per l'ordine non ci sono log. `angoli_arco` ha un elemento per ogni movimento del Carro: angolo letto subito prima della partenza e subito dopo l'arrivo (`null` se assente).

### `GET tracciabilita?qr_data=<codice>`

Equivalente JSON della pagina `/tracciamento/processqrcode/` (stessi calcoli). `qr_data` è il contenuto del QR code, in uno dei formati `262/3`, `IdRecord:262/3`, `id:262/3`, `262`: `262` è l'`id_record` della commessa, `3` il numero del pezzo (facoltativo).

```json
{
  "codice": "262",
  "pezzo": 3,
  "cliente": "GLAMOUR SOFA' S",
  "qualita": "Ottimo",
  "qualita_valutata": true,
  "scarto_x_mm": -0.12,
  "scarto_y_mm": 0.4,
  "commesse": [
    { "commessa": { "…": "Commessa" },
      "ordine":   { "…": "Ordine" },
      "macchina": { "…": "Macchina" },
      "controllo_qualita": { "esito": "Ottimo", "valutato": true, "scarto_x_mm": -0.12, "scarto_y_mm": 0.4 } }
  ],
  "articoli": [ { "…": "Articolo con volume e densità" } ]
}
```

- `qualita` / `esito`: `Ottimo`, `Rettificare` o `Scartare`. Quando non calcolabile contiene un messaggio (`Nessun log trovato per il valore specificato.`, `Dati insufficienti per calcolare la qualità`, `Soglie di qualità non configurate`) e `qualita_valutata`/`valutato` è `false`: i client devono basarsi su questi flag, non sul testo.
- Il controllo è eseguito sul pezzo `quantita_lavorata` (ultimo lavorato) di ciascuna commessa; il campo `qualita` di primo livello e gli scarti di primo livello riflettono l'**ultima** commessa valutata, come nella pagina web. Il dettaglio per commessa è in `commesse[].controllo_qualita`.
- `scarto_*_mm` sono `null` se non calcolabili.
- `404` se nessuna commessa (nel perimetro dell'utente) ha quell'`id_record`; `400` se `qr_data` manca.

### `GET qualita/soglie`
```json
{ "angolo_automatico": { "soglia_ottimo": 0.5, "soglia_rettifica": 1.0 }, "taglio": { "soglia_accettabile": 0.1 } }
```
Ogni gruppo è `null` se non configurato dall'admin.

## 6. Esempi

```bash
TOKEN=...   # ottenuto con crea_token_api

# Utente corrente
curl -H "Authorization: Bearer $TOKEN" https://host/api/v1/me

# Log di una macchina di aprile 2026, 500 per pagina
curl -H "Authorization: Bearer $TOKEN" \
  "https://host/api/v1/log?macchina=4&da=2026-04-01&a=2026-04-30&page_size=500"

# Report di tracciabilità da QR code
curl -H "Authorization: Bearer $TOKEN" "https://host/api/v1/tracciabilita?qr_data=262/3"
```

Scaricare un elenco completo in Python:

```python
import requests

BASE, HEADERS = "https://host/api/v1", {"Authorization": "Bearer <token>"}

def scarica(percorso, **filtri):
    pagina = 1
    while True:
        r = requests.get(f"{BASE}/{percorso}", headers=HEADERS,
                         params={**filtri, "page": pagina, "page_size": 500}, timeout=30)
        r.raise_for_status()
        dati = r.json()
        yield from dati["results"]
        if pagina >= dati["num_pages"]:
            return
        pagina += 1

log = list(scarica("log", macchina=4, da="2026-04-01"))
```

## 7. Note operative

- **Sicurezza**: usare sempre HTTPS (il token viaggia in chiaro nell'intestazione). Il token equivale alle credenziali dell'utente: tenerlo fuori dal codice e dal repository e revocarlo dall'admin se compromesso. Non c'è limitazione di frequenza (rate limit) a livello applicativo: se necessario applicarla sul reverse proxy.
- **Tabella `log`**: è la più grande; per estrazioni periodiche filtrare sempre per `macchina` e intervallo `da`/`a` e usare `page_size=500`.
- **Compatibilità**: la versione è nel percorso (`/v1/`). Aggiungere campi o endpoint non è considerato una modifica incompatibile; i client devono ignorare i campi sconosciuti.
- **Test**: `python manage.py test api` (autenticazione, perimetro per cliente, filtri, paginazione, tracciabilità).
