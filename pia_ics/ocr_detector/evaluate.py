"""Valutazione delle prestazioni su foto con testo atteso trascritto a mano.

Gli insiemi di foto, le pre-elaborazioni da confrontare e la cartella dei
risultati si indicano in settings.yaml (sezione `evaluation`). Ogni insieme
è elaborato con ogni pre-elaborazione:

* `datasets` (con ground truth): metriche stampate e salvate in CSV
  (vedi `evaluation/csv_report.py`);
* `visual_only` (senza ground truth): solo l'output di ogni foto, per il
  controllo visivo. Nessuna metrica: senza testo atteso non si può misurare.

Esecuzione, dalla cartella che CONTIENE `ocr_detector/` (cioè "PIA ICS"):

    ocr_detector\\.venv\\Scripts\\python.exe -m ocr_detector.evaluate

Per valutare nuove foto: trascriverne il testo in un file JSON nel formato
descritto in `evaluation/evaluator.py` e indicarlo in settings.yaml.
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from ocr_detector.evaluation.csv_report import write_comparison_csv
from ocr_detector.evaluation.csv_report import write_csv_reports
from ocr_detector.evaluation.evaluator import Evaluator
from ocr_detector.export.result_writer import ResultWriter
from ocr_detector.export.result_writer import preprocessing_folder
from ocr_detector.pipeline.ocr_engine import OcrEngine
from ocr_detector.pipeline.settings import Settings
from ocr_detector.pipeline.text_reader import TextReader

SETTINGS_PATH = Path(__file__).parent / "settings.yaml"


def main() -> None:
    logging.basicConfig(level=logging.WARNING, stream=sys.stderr)
    settings = Settings.from_yaml(SETTINGS_PATH)
    config = settings.section("evaluation")
    recognition = settings.section("recognition")
    engine = OcrEngine.from_settings(settings)
    evaluator = Evaluator()

    output_dir = settings.path(config["output_dir"])
    export = settings.section("export")
    preprocessings = config.get("preprocessings") or [recognition["preprocessing"]]

    comparison = []
    for preprocessing in preprocessings:
        # Cambia solo il passo 4 (lettura): rilevamento, ROI e raddrizzamento restano uguali.
        engine.reader = TextReader(engine.reader.model, preprocessing, recognition["try_upside_down"])

        for dataset in config["datasets"]:
            ground_truth = json.loads(settings.path(dataset["ground_truth"]).read_text(encoding="utf-8"))
            images_dir = settings.path(dataset["images_dir"])
            # Output di ogni foto (come inference.py) in risultati/preprocessing_X/<insieme>/<foto>/.
            writer = None
            if output_dir is not None:
                writer = ResultWriter.from_settings(
                    preprocessing_folder(output_dir, preprocessing) / dataset["name"], export)

            rows = []
            for name, reference in ground_truth.items():
                result = engine.process_file(images_dir / name)
                if writer is not None:
                    writer.write(result)
                rows.append(evaluator.evaluate(result, reference))
            summary = evaluator.summarize(rows)
            comparison.append({"dataset": dataset["name"], "preprocessing": preprocessing, **summary})

            print()
            print(f"=== {dataset['name']} - {preprocessing} ({len(rows)} foto) ===")
            _print_table(rows, summary)
            if output_dir is not None:
                for path in write_csv_reports(rows, summary, preprocessing_folder(output_dir, preprocessing),
                                              dataset["name"]):
                    print(f"Salvato: {path}")

        # Insiemi senza ground truth: solo output di ogni foto, nessuna metrica.
        for dataset in config.get("visual_only") or []:
            if output_dir is None:
                break
            writer = ResultWriter.from_settings(
                preprocessing_folder(output_dir, preprocessing) / dataset["name"], export)
            images = engine.loader.collect([settings.path(dataset["images_dir"])])
            for path in images:
                writer.write(engine.process_file(path))
            print(f"=== {dataset['name']} - {preprocessing}: {len(images)} foto elaborate "
                  f"(solo valutazione visiva) -> {writer.output_dir}")

    print()
    print("=== Confronto pre-elaborazioni ===")
    _print_comparison(comparison)
    if output_dir is not None:
        print(f"Salvato: {write_comparison_csv(comparison, output_dir)}")


def _print_table(rows: list[dict], summary: dict) -> None:
    print(f"{'foto':<40} {'CER':>7} {'testi':>7} {'err.testi':>9} {'princ.':>7} {'tempo':>7}")
    for r in rows:
        key = "-" if r["key"] is None else ("ok" if r["key_edits"] == 0 else f"{r['key_edits']} car.")
        print(f"{r['file'][-40:]:<40} {100 * r['edits'] / max(r['reference_chars'], 1):>6.1f}% "
              f"{r['fields_found']:>3}/{r['fields_total']:<3} "
              f"{100 * r['fields_edits'] / max(r['fields_chars'], 1):>8.1f}% {key:>7} {r['seconds']:>6.1f}s")
    print(f"{'TOTALE':<40} {summary['cer_pct']:>6.1f}% {summary['fields_found']:>3}/{summary['fields_total']:<3} "
          f"{summary['fields_cer_pct']:>8.1f}% {summary['key_in_text']:>4}/{summary['keys_total']} "
          f"{summary['mean_seconds']:>6.1f}s")


def _print_comparison(comparison: list[dict]) -> None:
    print(f"{'insieme':<20} {'preproc.':<8} {'CER':>7} {'testi':>9} {'err.testi':>9} {'tempo':>7}")
    for c in sorted(comparison, key=lambda c: c["dataset"]):
        print(f"{c['dataset']:<20} {c['preprocessing']:<8} {c['cer_pct']:>6.1f}% "
              f"{c['fields_found']:>4}/{c['fields_total']:<4} {c['fields_cer_pct']:>8.1f}% "
              f"{c['mean_seconds']:>6.1f}s")


if __name__ == "__main__":
    main()
