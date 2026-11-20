"""Punto di ingresso: legge le foto indicate in settings.yaml e stampa il testo.

Cosa elaborare e dove salvare si indicano in settings.yaml (sezione `run`).

Esecuzione, dalla cartella che CONTIENE `ocr_detector/` (cioè "PIA ICS"):

    ocr_detector\\.venv\\Scripts\\python.exe -m ocr_detector.main

Il risultato (JSON) va su stdout, i messaggi di log su stderr.

Da Python (es. in un servizio), senza passare da questo file:

    engine = OcrEngine.from_settings(Settings.from_yaml("ocr_detector/settings.yaml"))
    result = engine.process_file("foto.jpg")      # oppure engine.process_array(pixels)
    result.to_output()
"""
from __future__ import annotations

import json
import logging
import sys
from pathlib import Path

from ocr_detector.export.result_writer import ResultWriter
from ocr_detector.export.result_writer import preprocessing_folder
from ocr_detector.pipeline.ocr_engine import OcrEngine
from ocr_detector.pipeline.settings import Settings

SETTINGS_PATH = Path(__file__).parent / "settings.yaml"


def main() -> None:
    settings = Settings.from_yaml(SETTINGS_PATH)
    logging.basicConfig(level=settings.section("logging")["level"], stream=sys.stderr,
                        format="%(asctime)s %(levelname)-7s %(message)s")
    run = settings.section("run")

    engine = OcrEngine.from_settings(settings)
    output_dir = settings.path(run["output_dir"])
    if output_dir is not None:
        output_dir = preprocessing_folder(output_dir, settings.section("recognition")["preprocessing"])

    outputs = []
    for entry in run["images"]:
        source = settings.path(entry)
        # risultati/preprocessing_X/<cartella>/<foto>/: per un file singolo, la sua cartella.
        writer = None
        if output_dir is not None:
            folder = source.name if source.is_dir() else source.parent.name
            writer = ResultWriter.from_settings(output_dir / folder, settings.section("export"))

        for path in engine.loader.collect([source]):
            result = engine.process_file(path)
            if writer is not None:
                writer.write(result)
            outputs.append(result.to_output())
            logging.info("%s: %s", path.name, " | ".join(result.to_output()["text_lines"]) or "-")

    # Una foto -> un oggetto JSON; più foto -> una lista.
    print(json.dumps(outputs[0] if len(outputs) == 1 else outputs, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
