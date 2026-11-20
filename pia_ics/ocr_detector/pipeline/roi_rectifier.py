"""Raddrizzamento delle ROI."""
from __future__ import annotations

import math

import cv2
import numpy as np

from ocr_detector.pipeline.entities import RegionOfInterest
from ocr_detector.pipeline.entities import TextBox


class RoiRectifier:
    """Porta una ROI "in piano": righe orizzontali e altezza di riga standard.

    1. Direzione delle righe = direzione PREVALENTE dei box allungati.
       Prevalente e non media: se la ROI contiene anche scritte con un'altra
       inclinazione (es. loghi stampati in diagonale), la media darebbe un
       angolo che non corrisponde a nessuna delle due.
    2. Una sola trasformazione affine (rotazione + scala + traslazione) porta
       le righe in orizzontale e alla altezza `target_text_height`, che è
       quella in cui il riconoscitore lavora meglio.

    Il verso (dritto o capovolto) qui non si decide: lo sceglie `TextReader`
    leggendo la ROI nei due versi.
    """

    def __init__(self, direction_tolerance_deg: float = 10.0, min_line_aspect_ratio: float = 2.0,
                 target_text_height: float = 48.0, max_scale: float = 4.0,
                 padding_text_heights: float = 1.5, max_output_side: int = 4000):
        """
        Args:
            direction_tolerance_deg: Box con direzioni entro questa tolleranza
                sono considerati concordi.
            min_line_aspect_ratio: Solo i box più allungati di così indicano
                la direzione (un carattere isolato non ha direzione).
            target_text_height: Altezza di riga in uscita (px).
            max_scale: Ingrandimento massimo (oltre si interpola solo rumore).
            padding_text_heights: Margine attorno al testo, in altezze di riga.
            max_output_side: Lato massimo dell'immagine in uscita.
        """
        self.direction_tolerance_deg = direction_tolerance_deg
        self.min_line_aspect_ratio = min_line_aspect_ratio
        self.target_text_height = target_text_height
        self.max_scale = max_scale
        self.padding_text_heights = padding_text_heights
        self.max_output_side = max_output_side

    def rectify(self, pixels: np.ndarray, roi: RegionOfInterest) -> RegionOfInterest:
        """Raddrizza la ROI: valorizza `roi.image`, `roi.matrix`, `roi.text_angle`.

        Args:
            pixels: Foto originale BGR.
            roi: ROI da raddrizzare (modificata sul posto e restituita).
        """
        if not roi.text_boxes:
            # ROI "foto intera": nessuna trasformazione.
            roi.image, roi.matrix = pixels, np.float32([[1, 0, 0], [0, 1, 0]])
            return roi

        roi.text_angle = self._dominant_angle(roi.text_boxes)
        roi.matrix, size, scale = self._build_transform(roi.text_boxes, roi.text_angle)
        interpolation = cv2.INTER_CUBIC if scale > 1.0 else cv2.INTER_LINEAR
        roi.image = cv2.warpAffine(pixels, roi.matrix, size, flags=interpolation,
                                   borderMode=cv2.BORDER_REPLICATE)
        return roi

    def _dominant_angle(self, boxes: list[TextBox]) -> float:
        """Direzione prevalente delle righe, in gradi in (-90, 90].

        Le direzioni sono definite a meno di 180° (0° e 180° sono la stessa
        retta): per mediarle si raddoppiano gli angoli, si mediano i vettori
        unitari e si dimezza il risultato (179° e 1° -> 0°, non 90°).
        """
        angles, weights = [], []
        for box in boxes:
            p = box.polygon
            edge_a, edge_b = p[1] - p[0], p[2] - p[1]
            long_edge, short_edge = (edge_a, edge_b) if np.linalg.norm(edge_a) >= np.linalg.norm(edge_b) else (edge_b, edge_a)
            long_len, short_len = np.linalg.norm(long_edge), max(np.linalg.norm(short_edge), 1e-6)
            if long_len / short_len >= self.min_line_aspect_ratio:
                angles.append(math.degrees(math.atan2(long_edge[1], long_edge[0])))
                weights.append(long_len * box.score)   # righe lunghe e sicure contano di più
        if not angles:
            return 0.0
        angles, weights = np.array(angles), np.array(weights)

        # Per ogni box: peso del testo con direzione concorde (entro la tolleranza).
        difference = np.abs(angles[:, None] - angles[None, :]) % 180.0
        difference = np.minimum(difference, 180.0 - difference)
        concordant = difference <= self.direction_tolerance_deg
        members = concordant[int(np.argmax(concordant.astype(float) @ weights))]

        # Media "a angolo doppio" dei soli box del gruppo prevalente.
        mean_vector = np.sum(weights[members] * np.exp(2j * np.radians(angles[members])))
        return float(np.degrees(np.angle(mean_vector)) / 2.0)

    def _build_transform(self, boxes: list[TextBox], angle: float) -> tuple[np.ndarray, tuple[int, int], float]:
        """Matrice affine foto -> ROI raddrizzata.

        Si proiettano i vertici dei box sugli assi u (lungo le righe) e
        v (attraverso le righe), si prende il rettangolo che li contiene più un
        margine e lo si mappa sull'immagine di uscita, scalato.
        """
        theta = math.radians(angle)
        u = np.array([math.cos(theta), math.sin(theta)])
        v = np.array([-math.sin(theta), math.cos(theta)])

        points = np.concatenate([b.polygon for b in boxes]).astype(np.float64)
        center = points.mean(axis=0)
        along, across = (points - center) @ u, (points - center) @ v

        text_height = float(np.median([b.text_height for b in boxes]))
        margin = self.padding_text_heights * text_height
        u_min, u_max = along.min() - margin, along.max() + margin
        v_min, v_max = across.min() - margin, across.max() + margin

        scale = min(self.target_text_height / text_height, self.max_scale)
        longest_side = max(u_max - u_min, v_max - v_min) * scale
        if longest_side > self.max_output_side:
            scale *= self.max_output_side / longest_side

        size = (max(1, math.ceil((u_max - u_min) * scale)), max(1, math.ceil((v_max - v_min) * scale)))
        # x' = scale * ((p - center)·u - u_min),  y' = scale * ((p - center)·v - v_min)
        matrix = scale * np.array([[u[0], u[1], -center @ u - u_min],
                                   [v[0], v[1], -center @ v - v_min]])
        return matrix.astype(np.float32), size, scale
