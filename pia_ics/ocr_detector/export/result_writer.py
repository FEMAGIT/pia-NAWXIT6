"""Salvataggio su disco dei risultati (per il controllo visivo e il debug)."""
from __future__ import annotations

import json
import re
from pathlib import Path

import cv2
import numpy as np

from ocr_detector.pipeline.entities import ImageResult
from ocr_detector.export.result_visualizer import ResultVisualizer


def preprocessing_folder(output_dir: Path, preprocessing: str) -> Path:
    """Cartella dei risultati di una pre-elaborazione: risultati/preprocessing_<nome>/."""
    return Path(output_dir) / f"preprocessing_{preprocessing}"


class ResultWriter:
    """Scrive i risultati in una cartella:

        <output_dir>/<nome_foto>/
            result.json      risultato: testo letto, tempi
            debug.json       dettagli: ROI, posizione di ogni testo, tutti i box (se save_debug)
            overview.jpg    foto con ROI e box (se visualizer presente)
            roi_N.png        ROI raddrizzata con il testo letto (se visualizer presente)
            roi_N_preprocessed.png  la stessa dopo clahe/otsu, come la legge il modello
                                    (se visualizer presente e preprocessing non "none")
    """

    # Liste di soli numeri (coordinate) che json.dumps andrebbe a capo per ogni valore.
    _NUMBER_LIST = re.compile(r"\[\s*(-?[\d.]+(?:,\s*-?[\d.]+)*)\s*\]")

    def __init__(self, output_dir: Path, visualizer: ResultVisualizer | None = None, jpeg_quality: int = 90,
                 save_debug: bool = True):
        self.output_dir = Path(output_dir)
        self.visualizer = visualizer
        self.jpeg_quality = jpeg_quality
        self.save_debug = save_debug

    def write(self, result: ImageResult) -> Path:
        """Salva il risultato di una foto e restituisce la cartella usata."""
        destination = self.output_dir / result.image.stem
        destination.mkdir(parents=True, exist_ok=True)
        (destination / "result.json").write_text(self._dumps(result.to_output()), encoding="utf-8")
        if self.save_debug:
            (destination / "debug.json").write_text(self._dumps(result.to_debug()), encoding="utf-8")

        if self.visualizer is not None and result.image.pixels is not None:
            self._write_image(destination / "overview.jpg", self.visualizer.render_overview(result))
            for roi in result.rois:
                self._write_image(destination / f"roi_{roi.rank}.png", self.visualizer.render_roi(roi))
                if roi.prepared_image is not None:
                    self._write_image(destination / f"roi_{roi.rank}_preprocessed.png",
                                      self.visualizer.render_roi(roi, prepared=True))
        return destination

    @classmethod
    def from_settings(cls, output_dir: Path, export: dict) -> "ResultWriter":
        """Crea il writer dalla sezione `export` di settings.yaml."""
        return cls(
            output_dir   = output_dir,
            visualizer   = ResultVisualizer(max_overview_side=export["max_overview_side"]) if export["save_images"] else None,
            jpeg_quality = export["jpeg_quality"],
            save_debug   = export["save_debug"],
        )

    @classmethod
    def _dumps(cls, data: dict) -> str:
        """JSON indentato, ma con le coordinate su una riga: [570.4, 546.7]."""
        text = json.dumps(data, indent=2, ensure_ascii=False)
        text = cls._NUMBER_LIST.sub(lambda m: "[" + ", ".join(v.strip() for v in m.group(1).split(",")) + "]", text)
        # Poligoni: [[x, y], [x, y], ...] su una riga sola.
        return re.sub(r"\[\s*((?:\[[^\[\]]*\],?\s*)+)\]",
                      lambda m: "[" + ", ".join(re.findall(r"\[[^\[\]]*\]", m.group(1))) + "]", text)

    def _write_image(self, path: Path, image: np.ndarray) -> None:
        """Scrittura compatibile con percorsi non ASCII su Windows
        (`cv2.imwrite` li rifiuta): si codifica in memoria e si scrive il buffer."""
        params = [cv2.IMWRITE_JPEG_QUALITY, self.jpeg_quality] if path.suffix == ".jpg" else []
        ok, buffer = cv2.imencode(path.suffix, image, params)
        if not ok:
            raise IOError(f"Impossibile codificare {path}")
        buffer.tofile(str(path))
