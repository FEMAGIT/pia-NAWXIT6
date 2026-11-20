"""Lettura OCR di un'immagine (ROI raddrizzata), nel verso migliore."""
from __future__ import annotations

import cv2
import numpy as np

from ocr_detector.pipeline.ocr_model import OcrModel, Reading


class TextReader:
    """Legge il testo con il modello OCR (PP-OCRv4), scegliendo il verso.

    Il modello rileva le righe e le riconosce. Qui si aggiungono due cose:

    * pre-elaborazione CLAHE (contrasto locale), che non peggiora mai e
      spesso migliora; Otsu è disponibile ma cancella il testo inciso;
    * scelta del verso: la ROI raddrizzata può essere dritta o capovolta. Si
      legge in entrambi i versi e si tiene la lettura con qualità maggiore
      (somma di confidenza x caratteri): nel verso sbagliato il riconoscitore
      produce poche stringhe, corte e incerte.
    """

    PREPROCESSINGS = ("none", "clahe", "otsu")

    def __init__(self, model: OcrModel, preprocessing: str = "clahe", try_upside_down: bool = True):
        """
        Args:
            model: Modello OCR (si usa la sua operazione `read`).
            preprocessing: "none", "clahe" oppure "otsu".
            try_upside_down: Se True legge anche l'immagine capovolta.
        """
        if preprocessing not in self.PREPROCESSINGS:
            raise ValueError(f"preprocessing deve essere uno fra {self.PREPROCESSINGS}")
        self.preprocessing = preprocessing
        self.try_upside_down = try_upside_down
        self.model = model
        self._clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))

    def read(self, image: np.ndarray) -> tuple[list[tuple[np.ndarray, str, float]], int, np.ndarray]:
        """Legge l'immagine nel verso migliore.

        Args:
            image: Immagine BGR (di solito la ROI raddrizzata).

        Returns:
            tuple: (lista di (poligono in coordinate di `image`, testo, confidenza),
                    rotazione scelta: 0 o 180,
                    immagine pre-elaborata data al modello, nel verso originale)
        """
        prepared = self._preprocess(image)
        best, rotation = self._read_once(prepared), 0

        if self.try_upside_down:
            flipped = self._read_once(cv2.rotate(prepared, cv2.ROTATE_180))
            if self._quality(flipped) > self._quality(best):
                # Poligoni riportati nell'immagine non ruotata: (x, y) -> (W - x, H - y)
                height, width = image.shape[:2]
                best = [(np.float32([width, height]) - p, t, s) for p, t, s in flipped]
                rotation = 180
        return best, rotation, prepared

    def _read_once(self, image: np.ndarray) -> list[Reading]:
        """Una lettura con il modello, in un solo verso."""
        return self.model.read(image)

    def _preprocess(self, image: np.ndarray) -> np.ndarray:
        """Applica la pre-elaborazione configurata (restituisce sempre BGR)."""
        if self.preprocessing == "none":
            return image
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        if self.preprocessing == "clahe":
            gray = self._clahe.apply(gray)
        else:  # otsu
            gray = cv2.threshold(cv2.GaussianBlur(gray, (3, 3), 0), 0, 255,
                                 cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
        return cv2.cvtColor(gray, cv2.COLOR_GRAY2BGR)

    @staticmethod
    def _quality(texts: list[tuple[np.ndarray, str, float]]) -> float:
        """Qualità di una lettura: somma di confidenza x numero di caratteri."""
        return sum(score * len(text) for _, text, score in texts)
