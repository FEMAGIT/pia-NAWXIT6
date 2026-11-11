# Controllo qualità: ricostruzione della logica

## Scopo e perimetro

Questo documento ricostruisce il controllo qualità implementato nel modulo di tracciamento ICS. È basato sul codice corrente e sulla cronologia Git, non su una specifica di processo esterna. Serve quindi a ricordare sia l'intento operativo sia il comportamento reale dell'algoritmo.

L'implementazione è stata introdotta nel commit `5ef3b36` del 7 febbraio 2025, intitolato *Controllo qualità*.

## Flusso operativo

```text
Operatore autenticato
    -> apre “Tracciabilità”
    -> acquisisce il QR della commessa
    -> codice IdRecord
    -> Commessa + Ordine + Macchina + Articoli
    -> intervallo temporale dei log dell'ordine
    -> misure X, Y e alpha
    -> scostamenti e confronto con soglie
    -> esito mostrato nello storico
```

1. La voce di menu porta a `tracciamento:scanqrcode`.
2. La pagina di scansione legge il contenuto del QR e richiama `processqrcode/?qr_data=…`.
3. Se il QR usa il formato `IdRecord:<codice>`, viene estratto `<codice>`; altrimenti viene usato l'intero valore letto.
4. Il sistema cerca le `Commessa` con `id_record=<codice>`.
5. Per ciascuna commessa carica macchina, ordine e articolo/i del blocco; calcola anche la densità del blocco da dimensioni e peso per la schermata di storico.
6. Nella stessa elaborazione calcola un solo esito di qualità, esposto in alto nella pagina `storico.html`. L'esito non viene salvato in una tabella dedicata.

## Dati coinvolti

| Entità | Campi rilevanti | Ruolo |
| --- | --- | --- |
| `Commessa` | `id_record`, `id_macchina`, `dima`, `profondità`, `qtalav`, `qta`, `ordine` | Collega il QR, la geometria attesa e il ciclo di lavorazione. |
| `Ordine` | `id_ordine_esterno` | Identificatore cercato nel campo `Log.valore` per delimitare il ciclo. |
| `Log` | `timestamp`, `attività`, `input`, `valore` | Telemetria usata per ricavare le distanze X/Y e i valori alpha. |
| `Attività` | `tipo_attività` | Distingue `Movimentazione x`, `Movimentazione y` e `Movimentazione alpha`. |
| `QualitàAngoloAutomatico` | `soglia_ottimo`, `soglia_rettifica` | Soglie per la valutazione angolare. |
| `QualitàTaglio` | `soglia_accettabile` | Tolleranza percentuale/dimensionale usata sul taglio. |

Le soglie vengono lette dal primo record disponibile delle due tabelle, senza filtro per macchina, commessa, cliente o data. Per il calcolo sono pertanto necessari almeno un record `QualitàAngoloAutomatico` e uno `QualitàTaglio` con tutte le soglie valorizzate.

## Delimitazione del ciclo e selezione delle misure

Il codice cerca inizialmente tutti i `Log` per cui `valore` coincide con `Ordine.id_ordine_esterno`. Il timestamp minimo e massimo di questi log definiscono l'intervallo del ciclo.

All'interno dell'intervallo aperto `(min_timestamp, max_timestamp)` estrae:

- movimenti X con `input=1` e attività `Movimentazione x`;
- movimenti Y con `input=1` e attività `Movimentazione y`;
- movimenti alpha con attività `Movimentazione alpha`.

Per X e Y, per ogni indice da `0` a `qtalav - 1`, viene calcolata la differenza assoluta tra due log consecutivi. L'iterazione mantiene in pratica l'ultima differenza elaborata; l'ultima misura è trattata come differenza con la misura precedente. Le variabili `new_valx_left` e `new_valy_left` rappresentano il valore precedente quando disponibile.

Per alpha la selezione non usa timestamp o relazione esplicita: parte da ogni log Y e cerca i log alpha con ID rispettivamente `id - 1` e `id + 4`. Dai due valori costruisce `vala`, `new_vala` e `media_vala`, che sono poi usati per lo stato angolare.

## Geometria e scostamenti

La dima è interpretata come stringa `Y X`, separata dal carattere maiuscolo `X`:

```text
dima_y = primo valore della dima
dima_x = secondo valore della dima  (calcolato ma non usato)
dima_z = profondità della commessa

scarto_x = differenza_X - dima_z
scarto_y = differenza_Y - dima_y
```

Vengono calcolati anche `scarto_x_left` e `scarto_y_left` per il taglio precedente, salvo quando si tratta dell'ultima lavorazione: in quel caso è applicato il sentinella `99999` e il controllo precedente viene saltato.

## Regole di classificazione implementate

### Stato angolare

Il limite inferiore è `soglia_ottimo`; quello superiore è `soglia_rettifica`.

| Condizione effettiva | Stato |
| --- | --- |
| `media_vala <= soglia_ottimo` | `Ottimo` |
| `soglia_ottimo < media_vala < soglia_rettifica` | `Rettificare` |
| Tutti gli altri casi | `Scartare` |

Il codice esplicita quattro combinazioni di `vala` e `new_vala`, ma tutte producono `Ottimo` quando `media_vala` è entro la soglia ottima. In pratica, per questa parte della logica il discriminante decisivo è `media_vala`.

### Stato dimensionale e composizione dell'esito

Il limite dimensionale è:

```text
limite_x = profondità × soglia_accettabile
```

L'esito parziale conserva lo stato angolare solo se:

- `scarto_x <= 0`;
- `scarto_y >= 0`;
- per il taglio precedente, se disponibile, valgono le stesse condizioni.

In tutti gli altri casi l'esito è `Scartare`. Le condizioni confrontano anche `abs(scarto_x)` con `abs(limite_x)`, ma i due rami attualmente restituiscono lo stesso stato: nel comportamento corrente la grandezza dello scostamento X non cambia l'esito, mentre ne cambia il segno.

## Esiti e messaggi

| Esito | Significato applicativo |
| --- | --- |
| `Ottimo` | Angolo nella fascia ottima e condizioni dimensionali/sui tagli precedenti rispettate. |
| `Rettificare` | Angolo fra le due soglie, con condizioni dimensionali rispettate. |
| `Scartare` | Angolo fuori fascia o una condizione dimensionale non rispettata. |
| `Dati insufficienti per calcolare la qualità` | Non sono state ricavate tutte le misure necessarie. |
| `Nessun log trovato per il valore specificato.` | Non esiste alcun log ancora associato all'identificativo esterno dell'ordine. |

## Prerequisiti operativi impliciti

- Il QR deve contenere un `IdRecord` presente nella commessa.
- La commessa deve avere ordine, `id_macchina`, `qtalav`, `dima` nel formato `Y X` e `profondità` valorizzati.
- L'ordine deve avere `id_ordine_esterno` e i log di delimitazione devono riportarlo in `Log.valore`.
- Nel periodo delimitato devono esistere abbastanza log X, Y e alpha, nell'ordine previsto dal PLC.
- Gli ID dei log alpha devono rispettare gli offset relativi `-1` e `+4` rispetto ai log Y.
- Le tabelle delle soglie devono contenere dati validi prima della scansione.

## Limiti da ricordare

Questi non sono comportamenti desiderati dedotti dal dominio, ma osservazioni sul codice da tenere presenti quando si riprende il lavoro.

1. I log X/Y/alpha sono filtrati solo per intervallo temporale e tipo attività: non c'è un filtro esplicito sulla macchina o sulla commessa. Lavorazioni simultanee possono contaminare il calcolo.
2. L'associazione alpha usa ID incrementali dei log, non una chiave di correlazione o un timestamp. È fragile rispetto a inserimenti, ritardi e rigenerazioni dei log.
3. Non sono presenti controlli difensivi per una dima malformata, quantità mancanti o liste di log più corte del previsto.
4. Nel calcolo di `scarto_y_left` la condizione di confronto usa `dima_z`, ma la sottrazione usa `dima_y`; è verosimilmente un refuso da verificare.
5. Il ramo `if i == qtalav` nel ciclo alpha non è raggiungibile con `range(qtalav)`; merita revisione insieme alla gestione dell'ultimo pezzo.
6. `qta_totale`, `dima_x` e `tagli_totali` vengono calcolati o assegnati ma non incidono sul risultato.
7. Il risultato non è storicizzato: una variazione di soglie o di log può cambiare l'esito mostrato per una scansione già eseguita.

## Come riprendere il lavoro in sicurezza

Prima di modificare formule o soglie, fissare alcuni casi campione con input PLC, misure attese ed esito atteso. La sequenza consigliata è:

1. definire formalmente verso, unità e tolleranza di X, Y, Z e alpha;
2. associare ogni log a macchina, commessa e ciclo con una chiave esplicita;
3. estrarre il calcolo in una funzione pura e coprirlo con test per `Ottimo`, `Rettificare`, `Scartare` e dati incompleti;
4. sostituire il sentinella numerico con `None` o un valore strutturato;
5. salvare il risultato, le misure utilizzate, le soglie e la versione della regola in un record di controllo qualità;
6. rendere le soglie configurabili per macchina/tipologia e con periodo di validità.

## Riferimenti nel codice

- Ingresso e calcolo: `pia_ics/tracciamento/views.py`, classe `ProcessQRCodeView`.
- Modelli di processo e soglie: `pia_ics/struttura/models.py`.
- Rotte: `pia_ics/tracciamento/urls.py`.
- Presentazione dell'esito: `pia_ics/tracciamento/templates/storico.html`.
- Registrazione amministrativa delle soglie: `pia_ics/struttura/admin.py`.
