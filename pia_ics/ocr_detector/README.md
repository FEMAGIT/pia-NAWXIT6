# OCR Detector

Legge il testo da foto di etichette e targhette (cuscinetti, lame, motori, ...),
anche se l'oggetto è inclinato, decentrato o piccolo nell'inquadratura.

Restituisce **solo il testo letto**, riga per riga, senza interpretarlo.
Usa il modello OCR pre-addestrato PP-OCRv4 di PaddleOCR, eseguito con
onnxruntime tramite `rapidocr-onnxruntime`. Gira su CPU.

## Come funziona

1. **Trova il testo**: individua le zone della foto che contengono scritte.
2. **Raggruppa**: unisce le scritte vicine (es. le righe di un'etichetta).
3. **Raddrizza**: ruota ogni gruppo in modo che le righe siano orizzontali.
4. **Legge**: riconosce il testo, provando anche l'immagine capovolta.

## Installazione

Dalla cartella principale, con Python 3.11:

```powershell
py -3.11 -m venv ocr_detector\.venv
ocr_detector\.venv\Scripts\python.exe -m pip install -r ocr_detector\requirements.txt
```

## Configurazione

Tutto si imposta in `settings.yaml`:

- `run`: foto da elaborare (file o cartelle) e cartella dei risultati;
- `evaluation`: foto e testo atteso per la valutazione;
- le altre sezioni: parametri del modello e dei singoli passi.

## Uso

Indicare le foto in `settings.yaml`, poi:

```powershell
ocr_detector\.venv\Scripts\python.exe -m ocr_detector.main
```

Risultato per ogni foto:

```json
{
  "file": "foto.jpg",
  "error": null,
  "text_lines": ["DA2QTY 6205ZZC3", "26233", "SNR brand of NTN Group"],
  "timings_s": {"detection": 1.8, "reading": 1.3}
}
```

In `risultati/preprocessing_<X>/<cartella>/<foto>/` (X = la pre-elaborazione usata,
`recognition.preprocessing`; cartella = quella indicata in `run.images`) vengono salvati:

- `result.json`: il risultato qui sopra;
- `debug.json`: posizione di ogni testo nella foto (`export.save_debug`);
- `overview.jpg`, `roi_N.png`: immagini di controllo (`export.save_images`);
- `roi_N_preprocessed.png`: la stessa zona dopo la pre-elaborazione (clahe o otsu),
  cioè come la legge il modello (`export.save_images`, se il preprocessing non è `none`).

Con `save_debug: false` e `save_images: false` si salva solo `result.json`.

## Valutazione

```powershell
ocr_detector\.venv\Scripts\python.exe -m ocr_detector.evaluate
```

Esegue la pipeline con ogni pre-elaborazione in `evaluation.preprocessings`
(`none`, `clahe`, `otsu`):

- `evaluation.datasets`: foto **con** testo trascritto a mano (ground truth): output e
  metriche. Le misure si basano sulla distanza di Levenshtein (caratteri sbagliati,
  mancanti o in più);
- `evaluation.visual_only`: foto **senza** ground truth: solo l'output di ogni foto, per la
  valutazione visiva (nessuna metrica: senza testo atteso non si può misurare).

Risultati salvati in `risultati/`:

```text
risultati/
├── confronto_preprocessing.csv             # una riga per insieme e pre-elaborazione
├── preprocessing_clahe/
│   ├── <insieme>/<foto>/                   # output di ogni foto (come main.py)
│   ├── valutazione_<insieme>.csv           # una riga per foto, più il totale
│   └── valutazione_<insieme>_testi.csv  # una riga per testo atteso
├── preprocessing_none/                     # stessa struttura
└── preprocessing_otsu/
```

Insiemi con ground truth:

- `val_images`: 5 foto del progetto, testo trascritto a mano (38 testi attesi: righe e campi dell'etichetta);
- `mpsc`: 50 foto di parti metalliche dal dataset pubblico
  [MPSC](https://github.com/TongkunGuan/RFN/blob/main/IndustrialTextDataset.md),
  testo atteso dalle annotazioni ufficiali del dataset (239 parole, ognuna è un testo atteso).

| Insieme | Pre-elaborazione | CER | Errore sui testi | Testi senza errori | Tempo medio |
|---|---|---|---|---|---|
| `val_images` | `none` | 10.5 % | 3.1 % | 29 / 38 | ~3.5 s |
| `val_images` | `clahe` | **9.7 %** | 3.1 % | **30 / 38** | ~2.9 s |
| `val_images` | `otsu` | 20.9 % | 17.1 % | 20 / 38 | ~2.8 s |
| `mpsc` | `none` | 32.1 % | 14.9 % | **166 / 239** | ~1.6 s |
| `mpsc` | `clahe` | **30.7 %** | **14.7 %** | 161 / 239 | ~1.5 s |
| `mpsc` | `otsu` | 75.3 % | 66.1 % | 34 / 239 | ~1.1 s |


## Struttura

```text
ocr_detector/
├── main.py                   # avvio: legge le foto e stampa il testo
├── evaluate.py               # avvio: valutazione sulle foto di test
├── settings.yaml             # tutti i parametri
│
├── pipeline/                 # il processo di lettura
│   ├── ocr_engine.py         #   motore: esegue i 4 passi in ordine
│   ├── text_detector.py      #   1. trova il testo
│   ├── roi_builder.py        #   2. raggruppa
│   ├── roi_rectifier.py      #   3. raddrizza
│   ├── text_reader.py        #   4. legge
│   ├── ocr_model.py          #   modello OCR (PP-OCRv4)
│   ├── entities.py           #   strutture dati
│   ├── image_loader.py       #   lettura delle foto
│   └── settings.py           #   lettura di settings.yaml
│
├── export/                   # codice che scrive i file in risultati/ (JSON, immagini)
├── evaluation/               # calcolo delle misure, testo atteso (ground truth)
├── images/
│   ├── val_images/           # 5 foto con testo trascritto (ground truth): metriche
│   ├── original/             # 9 foto del progetto, senza ground truth: valutazione visiva
│   └── mpsc/                 # 50 foto di parti metalliche (MPSC), ground truth dalle annotazioni
├── risultati/                # solo dati: creata all'esecuzione
```
