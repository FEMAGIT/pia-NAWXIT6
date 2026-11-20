"""Caricamento delle foto da disco."""
from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

from ocr_detector.pipeline.entities import InputImage


class ImageLoader:
    """Carica una foto da file e risolve l'elenco dei file da elaborare.

    Il caricamento passa da Pillow invece che da `cv2.imread` per due motivi:
      * applica l'orientamento EXIF (le foto da smartphone sono spesso salvate
        "di lato" con un'indicazione su come ruotarle);
      * gestisce percorsi Windows con caratteri non ASCII.
    """

    def __init__(self, extensions: list[str]):
        """
        Args:
            extensions: Estensioni accettate quando si passa una cartella.
        """
        self.extensions = {e.lower() for e in extensions}

    def load(self, path: Path) -> InputImage:
        """Carica una foto.

        Raises:
            FileNotFoundError: Se il file non esiste.
        """
        path = Path(path)
        if not path.is_file():
            raise FileNotFoundError(f"Immagine non trovata: {path}")
        with Image.open(path) as pil_image:
            rgb = np.array(ImageOps.exif_transpose(pil_image).convert("RGB"))
        return InputImage(path=path, pixels=cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))

    def collect(self, paths: list[Path]) -> list[Path]:
        """Espande l'input in un elenco di file.

        Ogni voce può essere un file (preso così com'è) o una cartella (se ne
        prendono le immagini, anche nelle sottocartelle). Comodo per provare
        su un insieme di foto; in produzione si passa di norma un solo file.
        """
        files: list[Path] = []
        for path in map(Path, paths):
            if path.is_dir():
                files.extend(sorted(p for p in path.rglob("*")
                                    if p.is_file() and p.suffix.lower() in self.extensions))
            else:
                files.append(path)
        return files
