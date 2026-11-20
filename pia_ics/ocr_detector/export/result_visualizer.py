"""Immagini di controllo per la verifica visiva."""
from __future__ import annotations

import cv2
import numpy as np

from ocr_detector.pipeline.entities import ImageResult
from ocr_detector.pipeline.entities import RegionOfInterest


class ResultVisualizer:
    """Disegna due tipi di immagine di controllo:

    * `render_overview`: la foto con i box di testo (grigio) e le ROI
      (verde = principale, arancio/blu = secondarie);
    * `render_roi`: la ROI raddrizzata, nel verso di lettura, con i testi letti
      riquadrati e, sotto, il testo riconosciuto riga per riga; anche nella
      versione pre-elaborata (clahe/otsu), cioè come la vede il modello.
    """

    ROI_COLORS = [(0, 200, 0), (0, 140, 255), (255, 120, 0)]
    BOX_COLOR = (160, 160, 160)

    def __init__(self, max_overview_side: int = 1600, max_roi_width: int = 1200):
        self.max_overview_side = max_overview_side
        self.max_roi_width = max_roi_width

    def render_overview(self, result: ImageResult) -> np.ndarray:
        image = result.image.pixels
        scale = min(1.0, self.max_overview_side / max(image.shape[:2]))
        canvas = cv2.resize(image, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        thickness = max(1, round(max(canvas.shape[:2]) / 800))

        for box in result.text_boxes:
            cv2.polylines(canvas, [np.int32(box.polygon * scale)], True, self.BOX_COLOR, thickness)
        for roi in reversed(result.rois):   # la principale disegnata per ultima, in primo piano
            color = self.ROI_COLORS[min(max(roi.rank, 1), len(self.ROI_COLORS)) - 1]
            points = np.int32(roi.polygon * scale)
            cv2.polylines(canvas, [points], True, color, 3 * thickness)
            top = points[np.argmin(points[:, 1])]
            cv2.putText(canvas, f"ROI {roi.rank}", (int(top[0]), max(15, int(top[1]) - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6 * thickness, color, thickness + 1, cv2.LINE_AA)
        return canvas

    def render_roi(self, roi: RegionOfInterest, prepared: bool = False) -> np.ndarray:
        """prepared=True: disegna sull'immagine pre-elaborata (quella letta dal modello)."""
        source = roi.prepared_image if prepared else roi.image
        image = source if roi.rotation == 0 else cv2.rotate(source, cv2.ROTATE_180)
        height, width = image.shape[:2]
        canvas = image.copy()
        for text in roi.texts:
            polygon = text.polygon if roi.rotation == 0 else np.float32([width, height]) - text.polygon
            cv2.polylines(canvas, [np.int32(polygon)], True, (0, 170, 0), 2)

        scale = min(1.0, self.max_roi_width / width)
        canvas = cv2.resize(canvas, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)

        lines = roi.lines or ["(nessun testo letto)"]
        panel = np.full((28 * len(lines) + 10, max(canvas.shape[1], 300), 3), 255, np.uint8)
        for index, line in enumerate(lines, start=1):
            # I font di OpenCV sono solo ASCII: il testo completo è in result.json.
            ascii_line = "".join(c if 32 <= ord(c) < 127 else "?" for c in line)
            cv2.putText(panel, ascii_line, (6, 28 * index), cv2.FONT_HERSHEY_SIMPLEX, 0.65,
                        (20, 20, 20), 1, cv2.LINE_AA)
        canvas = cv2.copyMakeBorder(canvas, 0, 0, 0, panel.shape[1] - canvas.shape[1],
                                    cv2.BORDER_CONSTANT, value=(255, 255, 255))
        return np.vstack([canvas, panel])
