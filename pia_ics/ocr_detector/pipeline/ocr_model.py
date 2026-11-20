"""Modello OCR: PP-OCRv4 (PaddleOCR) eseguito con onnxruntime tramite rapidocr.

`rapidocr-onnxruntime` contiene gli stessi modelli PP-OCRv4 di PaddleOCR,
convertiti in formato ONNX: si eseguono con onnxruntime invece che con il
framework PaddlePaddle (più leggero, solo CPU, modelli inclusi nel pacchetto).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import rapidocr_onnxruntime
from rapidocr_onnxruntime import RapidOCR
from rapidocr_onnxruntime.ch_ppocr_v3_det import TextDetector

# (poligono 4x2, confidenza)
Detection = tuple[np.ndarray, float]
# (poligono 4x2, testo, confidenza)
Reading = tuple[np.ndarray, str, float]


class OcrModel:
    """PP-OCRv4: rilevamento (DBNet) e lettura (SVTR-LCNet).

    Offre le due operazioni usate dalla pipeline (immagini BGR, OpenCV):
      * detect(immagine) -> dove c'è testo   (passo 1, `TextDetector`)
      * read(immagine)   -> testo letto      (passo 4, `TextReader`)
    """

    def __init__(self, limit_side_len: int = 1280, binarization_threshold: float = 0.3,
                 box_threshold: float = 0.5, unclip_ratio: float = 1.6,
                 read_limit_side_len: int = 2000, text_score: float = 0.5, num_threads: int = -1):
        """
        Args:
            limit_side_len: Lato massimo dell'immagine data al detector (passo 1).
            binarization_threshold: Soglia sulla mappa di probabilità del testo.
            box_threshold: Confidenza minima di un box.
            unclip_ratio: Espansione del box attorno al testo.
            read_limit_side_len: Lato massimo nella lettura (passo 4). Si riduce
                solo se più grande: la ROI è già a scala giusta.
            text_score: Confidenza minima per tenere un testo letto.
            num_threads: Thread di onnxruntime (-1 = automatico).
        """
        model_path = Path(rapidocr_onnxruntime.__file__).parent / "models" / "ch_PP-OCRv4_det_infer.onnx"
        self._detector = TextDetector({
            "model_path": str(model_path),
            "limit_side_len": limit_side_len,
            "limit_type": "max",                 # riduce solo le immagini più grandi del limite
            "thresh": binarization_threshold,
            "box_thresh": box_threshold,
            "unclip_ratio": unclip_ratio,
            "max_candidates": 1000,
            "use_dilation": True,
            "score_mode": "fast",
            "use_cuda": False,
            "use_dml": False,
            "intra_op_num_threads": num_threads,
            "inter_op_num_threads": num_threads,
        })
        self._reader = RapidOCR(det_limit_side_len=read_limit_side_len, det_limit_type="max",
                                text_score=text_score, intra_op_num_threads=num_threads,
                                inter_op_num_threads=num_threads)

    def detect(self, image: np.ndarray) -> list[Detection]:
        """Trova le righe di testo, con la confidenza di ogni box."""
        # I tre stadi chiamati separatamente per conservare la confidenza di ogni box.
        network_input = self._detector.preprocess_op(image)
        if network_input is None:
            return []
        probability_map = self._detector.infer(network_input)[0]
        polygons, scores = self._detector.postprocess_op(probability_map, image.shape[:2])
        return [(np.asarray(p, np.float32), float(s)) for p, s in zip(polygons, scores)]

    def read(self, image: np.ndarray) -> list[Reading]:
        """Trova e legge il testo."""
        # Senza il classificatore di verso: il verso lo decide TextReader.
        result, _ = self._reader(image, use_cls=False)
        return [(np.asarray(p, np.float32), str(t), float(s)) for p, t, s in (result or [])]
