"""Rilevamento delle zone di testo, con inferenza a blocchi (tiling)."""
from __future__ import annotations

import cv2
import numpy as np

from ocr_detector.pipeline.entities import TextBox
from ocr_detector.pipeline.ocr_model import OcrModel


class TextDetector:
    """Trova dove c'è testo nella foto, come quadrilateri orientati (`TextBox`).

    Il rilevamento vero e proprio lo fa il modello OCR (`OcrModel`, PP-OCRv4).

    Inferenza a blocchi (tiling): i detector lavorano a ~1000-2500 px. Una
    foto da 12 MP ridotta a quella misura rende il testo di una piccola
    etichetta troppo minuto per essere visto. Per questo, oltre alla foto
    intera, si analizzano tile sovrapposte a piena risoluzione; i box visti
    più volte vengono poi uniti.
    """

    def __init__(self, model: OcrModel, tile_size: int = 1024, tile_overlap: float = 0.25,
                 duplicate_overlap: float = 0.6):
        """
        Args:
            model: Modello OCR (si usa la sua operazione `detect`).
            tile_size: Lato delle tile in pixel (0 = tiling disattivato).
            tile_overlap: Sovrapposizione fra tile adiacenti (frazione), per non
                perdere le righe tagliate al bordo di una tile.
            duplicate_overlap: Un box contenuto per più di questa frazione
                della sua area in un box più grande è un duplicato.
        """
        self._model = model
        self.tile_size = tile_size
        self.tile_overlap = tile_overlap
        self.duplicate_overlap = duplicate_overlap

    def detect(self, pixels: np.ndarray) -> list[TextBox]:
        """Trova il testo nella foto.

        Args:
            pixels: Foto BGR.

        Returns:
            list[TextBox]: Box di testo in coordinate della foto.
        """
        boxes = self._detect_once(pixels)
        height, width = pixels.shape[:2]
        if self.tile_size <= 0 or max(height, width) <= self.tile_size:
            return boxes

        for x0, y0 in self._tile_origins(width, height):
            tile = pixels[y0:y0 + self.tile_size, x0:x0 + self.tile_size]
            boxes += [b.translated(x0, y0) for b in self._detect_once(tile)]
        return self._remove_duplicates(boxes)

    def _detect_once(self, pixels: np.ndarray) -> list[TextBox]:
        """Una passata del modello, con i box limitati ai bordi dell'immagine."""
        height, width = pixels.shape[:2]
        boxes = []
        for polygon, score in self._model.detect(pixels):
            polygon = np.asarray(polygon, np.float32).copy()
            polygon[:, 0] = np.clip(polygon[:, 0], 0, width - 1)
            polygon[:, 1] = np.clip(polygon[:, 1], 0, height - 1)
            box = TextBox(polygon, float(score))
            if box.text_height > 3:   # box degeneri dopo il clipping ai bordi
                boxes.append(box)
        return boxes
    def _tile_origins(self, width: int, height: int) -> list[tuple[int, int]]:
        """Angolo alto-sinistro di ogni tile. L'ultima tile di ogni riga e
        colonna è appoggiata al bordo, così l'immagine è coperta per intero."""
        stride = max(1, int(self.tile_size * (1.0 - self.tile_overlap)))

        def positions(length: int) -> list[int]:
            last = max(0, length - self.tile_size)
            return sorted(set(list(range(0, last, stride)) + [last]))

        return [(x, y) for y in positions(height) for x in positions(width)]

    def _remove_duplicates(self, boxes: list[TextBox]) -> list[TextBox]:
        """Elimina i box già contenuti in un box più grande.

        Si confronta l'intersezione con l'area del box PIÙ PICCOLO (non la IoU):
        così si eliminano anche i frammenti di parola tagliati al bordo di una
        tile, che hanno IoU bassa con la parola intera ma vi sono contenuti.
        """
        kept: list[TextBox] = []
        for candidate in sorted(boxes, key=lambda b: b.area, reverse=True):
            duplicate = False
            for big in kept:
                intersection, _ = cv2.intersectConvexConvex(candidate.polygon, big.polygon)
                if intersection / max(candidate.area, 1e-6) > self.duplicate_overlap:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(candidate)
        return kept
