"""Strutture dati della pipeline (solo dati, nessuna elaborazione)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import cv2
import numpy as np


@dataclass(eq=False)
class InputImage:
    """Foto in memoria, già orientata correttamente.

    Attributes:
        path: File di provenienza. Per immagini arrivate da memoria (es. da una
            telecamera o da una richiesta HTTP) è solo un nome identificativo.
        pixels: Matrice BGR (convenzione OpenCV), shape (H, W, 3), uint8.
            None se il caricamento è fallito.
    """

    path: Path
    pixels: np.ndarray | None = field(default=None, repr=False)

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem

    @property
    def height(self) -> int:
        return int(self.pixels.shape[0])

    @property
    def width(self) -> int:
        return int(self.pixels.shape[1])


@dataclass(eq=False)
class TextBox:
    """Quadrilatero orientato che contiene una riga/parola di testo.

    Attributes:
        polygon: Array (4, 2) float32 con i vertici, in coordinate della foto.
        score: Confidenza del detector, in [0, 1].
    """

    polygon: np.ndarray = field(repr=False)
    score: float

    def __post_init__(self):
        # Le funzioni OpenCV usate dopo richiedono float32.
        self.polygon = np.asarray(self.polygon, dtype=np.float32).reshape(4, 2)

    @property
    def rotated_rect(self) -> tuple:
        """Rettangolo ruotato minimo ((cx, cy), (w, h), angolo) di OpenCV."""
        return cv2.minAreaRect(self.polygon)

    @property
    def text_height(self) -> float:
        """Altezza della riga = lato corto del box.

        È l'unità di misura usata per distanze e margini: rende i parametri
        indipendenti dalla risoluzione della foto.
        """
        (_, _), (w, h), _ = self.rotated_rect
        return float(max(1.0, min(w, h)))

    @property
    def area(self) -> float:
        return float(cv2.contourArea(self.polygon))

    def translated(self, dx: float, dy: float) -> "TextBox":
        """Copia traslata (per riportare i box di una tile sulla foto intera)."""
        return TextBox(self.polygon + np.float32([dx, dy]), self.score)

    def to_dict(self) -> dict:
        return {
            "polygon": [[round(float(x), 1), round(float(y), 1)] for x, y in self.polygon],
            "score": round(self.score, 4),
        }


@dataclass(eq=False)
class RecognizedText:
    """Una riga (o parte di riga) letta dall'OCR.

    Attributes:
        text: Testo riconosciuto.
        score: Confidenza del riconoscitore, in [0, 1].
        polygon: Quadrilatero (4, 2) nell'immagine raddrizzata della ROI.
        polygon_original: Lo stesso quadrilatero nella foto originale.
    """

    text: str
    score: float
    polygon: np.ndarray = field(repr=False)
    polygon_original: np.ndarray = field(repr=False)

    @property
    def center_x(self) -> float:
        return float(self.polygon[:, 0].mean())

    @property
    def center_y(self) -> float:
        return float(self.polygon[:, 1].mean())

    @property
    def height(self) -> float:
        return float(np.linalg.norm(self.polygon[3] - self.polygon[0]))

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "score": round(self.score, 4),
            "polygon_original": [[round(float(x), 1), round(float(y), 1)] for x, y in self.polygon_original],
        }


@dataclass(eq=False)
class RegionOfInterest:
    """Zona della foto con un gruppo di righe di testo vicine.

    La ROI è definita come "gruppo di righe vicine" e non come "rettangolo
    bianco": così vale per etichette adesive, targhe metalliche e scritte
    incise su un cuscinetto.

    L'oggetto si arricchisce lungo la pipeline:
      * `RoiBuilder`   -> text_boxes, polygon, rank
      * `RoiRectifier` -> image, matrix, text_angle
      * `TextReader`   -> texts, rotation, prepared_image

    Attributes:
        text_boxes: Box di testo del gruppo (vuoto per la ROI "foto intera").
        polygon: Contorno della ROI nella foto (per disegnarla).
        rank: Posizione in classifica (1 = più rilevante, 0 = foto intera).
        image: ROI raddrizzata: righe orizzontali, altezza di riga normalizzata.
        matrix: Matrice affine 2x3 foto -> `image`.
        text_angle: Inclinazione delle righe nella foto, in gradi.
        rotation: 0 o 180: rotazione con cui la ROI è stata letta meglio.
        texts: Testi letti dall'OCR.
        prepared_image: `image` dopo la pre-elaborazione (clahe/otsu), cioè
            quello che il modello ha letto; None se la pre-elaborazione è "none".
    """

    text_boxes: list[TextBox] = field(repr=False)
    polygon: np.ndarray = field(repr=False)
    rank: int = 0
    image: np.ndarray | None = field(default=None, repr=False)
    matrix: np.ndarray | None = field(default=None, repr=False)
    text_angle: float = 0.0
    rotation: int = 0
    texts: list[RecognizedText] = field(default_factory=list, repr=False)
    prepared_image: np.ndarray | None = field(default=None, repr=False)

    @classmethod
    def from_text_boxes(cls, text_boxes: list[TextBox]) -> "RegionOfInterest":
        """ROI che racchiude un gruppo di box (rettangolo orientato minimo)."""
        points = np.concatenate([b.polygon for b in text_boxes])
        return cls(text_boxes=text_boxes, polygon=cv2.boxPoints(cv2.minAreaRect(points)).astype(np.float32))

    @classmethod
    def whole_image(cls, image_shape: tuple[int, ...]) -> "RegionOfInterest":
        """ROI che coincide con l'intera foto (usata quando non si trova nessuna ROI)."""
        height, width = image_shape[:2]
        corners = np.float32([[0, 0], [width - 1, 0], [width - 1, height - 1], [0, height - 1]])
        return cls(text_boxes=[], polygon=corners, rank=0)

    @property
    def relevance(self) -> float:
        """Punteggio per ordinare le ROI: somma delle confidenze dei box.

        Premia le zone con più testo rilevato con sicurezza. Serve solo a
        ORDINARE le ROI (e a scegliere quali leggere se sono più di `max_rois`):
        tutte le ROI lette contribuiscono al risultato.
        """
        return float(sum(b.score for b in self.text_boxes))

    @property
    def scored_lines(self) -> list[tuple[str, float]]:
        """Testo letto ricomposto in righe, con la confidenza OCR di ogni riga.

        Testi con centri verticali distanti meno di metà altezza di riga
        stanno sulla stessa riga (l'OCR a volte spezza una riga in più pezzi).
        La confidenza della riga è quella del suo pezzo MENO sicuro.

        Returns:
            list[tuple[str, float]]: (riga, confidenza), dall'alto in basso.
        """
        rows: list[list[RecognizedText]] = []
        for text in sorted(self.texts, key=lambda t: t.center_y):
            if rows and abs(text.center_y - rows[-1][0].center_y) < 0.5 * max(text.height, 1.0):
                rows[-1].append(text)
            else:
                rows.append([text])
        return [(" ".join(t.text for t in sorted(row, key=lambda t: t.center_x)), min(t.score for t in row))
                for row in rows]

    @property
    def lines(self) -> list[str]:
        """Testo letto ricomposto in righe (alto -> basso, sinistra -> destra)."""
        return [line for line, _ in self.scored_lines]

    def to_original(self, points: np.ndarray) -> np.ndarray:
        """Riporta punti dell'immagine raddrizzata nelle coordinate della foto."""
        inverse = cv2.invertAffineTransform(self.matrix)
        return cv2.transform(np.asarray(points, np.float32).reshape(-1, 1, 2), inverse).reshape(-1, 2)

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "relevance": round(self.relevance, 3),
            "n_text_boxes": len(self.text_boxes),
            "polygon": [[round(float(x), 1), round(float(y), 1)] for x, y in self.polygon],
            "text_angle": round(self.text_angle, 2),
            "rotation": self.rotation,
            "lines": self.lines,
            "texts": [t.to_dict() for t in self.texts],
        }


@dataclass(eq=False)
class ImageResult:
    """Risultato completo per una singola foto.

    Attributes:
        image: Foto analizzata.
        text_boxes: Tutti i box di testo trovati (anche fuori dalle ROI).
        rois: ROI lette, ordinate per rilevanza. Se non ne è stata trovata
            nessuna, una sola ROI "foto intera" (rank 0).
        timings: Tempi di elaborazione in secondi per fase.
        error: Messaggio di errore se l'elaborazione è fallita.
    """

    image: InputImage
    text_boxes: list[TextBox] = field(default_factory=list, repr=False)
    rois: list[RegionOfInterest] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    error: str | None = None

    @property
    def main_roi(self) -> RegionOfInterest | None:
        return self.rois[0] if self.rois else None

    def to_output(self) -> dict:
        """Risposta compatta per chi usa il risultato (es. in produzione):
        testo letto (righe, dall'alto in basso), tempi, eventuale errore."""
        return {
            "file": self.image.name,
            "error": self.error,
            "text_lines": [line for roi in self.rois for line in roi.lines],
            "timings_s": {k: round(v, 3) for k, v in self.timings.items()},
        }

    def to_debug(self) -> dict:
        """Dettagli per il debug (ROI, testi con posizione, tutti i box), da
        affiancare a `to_output()`: non ne ripete il contenuto."""
        return {
            "file": self.image.name,
            "size_wh": [self.image.width, self.image.height] if self.image.pixels is not None else None,
            "rois": [r.to_dict() for r in self.rois],
            "all_text_boxes": [b.to_dict() for b in self.text_boxes],
        }
