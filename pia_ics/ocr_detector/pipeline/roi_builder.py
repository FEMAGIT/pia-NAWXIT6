"""Raggruppamento dei box di testo in regioni di interesse."""
from __future__ import annotations

import cv2

from ocr_detector.pipeline.entities import RegionOfInterest
from ocr_detector.pipeline.entities import TextBox


class RoiBuilder:
    """Raggruppa i box di testo vicini in ROI e le ordina per rilevanza.

    * Due box sono vicini se distano meno di `grouping_distance` altezze di
      riga. L'altezza di riga come unità rende il criterio indipendente dalla
      risoluzione della foto e dalla grandezza del testo.
    * I gruppi sono le componenti connesse del grafo "box vicini": catene di
      righe vicine formano un solo gruppo.
    * Nessun filtro sul contenuto: anche una ROI con una sola riga è valida
      (un'etichetta può avere un solo codice stampato). Il rumore viene
      scartato più avanti: se l'OCR non legge nulla, la ROI non produce testo.
    """

    def __init__(self, grouping_distance: float = 2.0, max_rois: int = 40):
        """
        Args:
            grouping_distance: Distanza massima fra due box dello stesso
                gruppo, in altezze di riga. Nei testi stampati lo spazio fra
                due righe è tipicamente 0.2-0.5 altezze di riga; 2 lascia
                margine per colonne e righe più spaziate senza unire scritte
                lontane.
            max_rois: Numero massimo di ROI lette per foto (le più rilevanti):
                limita il tempo di elaborazione su foto con molto testo sparso.
        """
        self.grouping_distance = grouping_distance
        self.max_rois = max_rois

    def build(self, boxes: list[TextBox]) -> list[RegionOfInterest]:
        """Costruisce le ROI, ordinate per rilevanza (rank 1 = più rilevante)."""
        rois = sorted((RegionOfInterest.from_text_boxes(g) for g in self._group(boxes)),
                      key=lambda r: r.relevance, reverse=True)[:self.max_rois]
        for rank, roi in enumerate(rois, start=1):
            roi.rank = rank
        return rois

    def _group(self, boxes: list[TextBox]) -> list[list[TextBox]]:
        """Componenti connesse del grafo "box vicini" (union-find)."""
        parent = list(range(len(boxes)))

        def root(i: int) -> int:
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                if self._are_neighbours(boxes[i], boxes[j]):
                    parent[root(i)] = root(j)

        groups: dict[int, list[TextBox]] = {}
        for index, box in enumerate(boxes):
            groups.setdefault(root(index), []).append(box)
        return list(groups.values())

    def _are_neighbours(self, a: TextBox, b: TextBox) -> bool:
        """True se i due box distano meno di `grouping_distance` altezze di riga:
        si allargano entrambi i rettangoli orientati e si controlla se si toccano."""
        margin = self.grouping_distance * min(a.text_height, b.text_height)
        (ca, (wa, ha), angle_a), (cb, (wb, hb), angle_b) = a.rotated_rect, b.rotated_rect
        intersection, _ = cv2.rotatedRectangleIntersection(
            (ca, (wa + margin, ha + margin), angle_a), (cb, (wb + margin, hb + margin), angle_b))
        return intersection != cv2.INTERSECT_NONE
