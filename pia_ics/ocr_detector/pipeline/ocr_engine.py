"""Motore OCR: da una foto al testo letto."""
from __future__ import annotations

import logging
import time
from pathlib import Path

import numpy as np

from ocr_detector.pipeline.settings import Settings
from ocr_detector.pipeline.image_loader import ImageLoader
from ocr_detector.pipeline.ocr_model import OcrModel
from ocr_detector.pipeline.text_detector import TextDetector
from ocr_detector.pipeline.entities import ImageResult
from ocr_detector.pipeline.entities import InputImage
from ocr_detector.pipeline.entities import RecognizedText
from ocr_detector.pipeline.entities import RegionOfInterest
from ocr_detector.pipeline.text_reader import TextReader
from ocr_detector.pipeline.roi_builder import RoiBuilder
from ocr_detector.pipeline.roi_rectifier import RoiRectifier

logger = logging.getLogger(__name__)


class OcrEngine:
    """Elabora UNA foto alla volta, scelta da chi lo usa.

    Pensato per la produzione: i modelli vengono caricati UNA volta alla
    creazione dell'oggetto (operazione lenta), poi si chiama `process_file`
    (foto su disco) o `process_array` (foto già in memoria, es. da una
    telecamera o da una richiesta HTTP) quante volte serve.

        engine = OcrEngine.from_settings(Settings.from_yaml("settings.yaml"))
        result = engine.process_file("foto.jpg")
        print(result.to_output())

    Passi, per ogni foto:
        1. TextDetector   -> dove c'è testo (box orientati, con tiling)
        2. RoiBuilder     -> box vicini raggruppati in ROI, ordinate per rilevanza
        3. RoiRectifier   -> ogni ROI raddrizzata e portata a scala standard
        4. TextReader     -> lettura OCR nel verso migliore (0° o 180°)
    Se il passo 2 non trova nessuna ROI, si legge la foto intera.
    """

    def __init__(self, loader: ImageLoader, detector: TextDetector, roi_builder: RoiBuilder,
                 rectifier: RoiRectifier, reader: TextReader,
                 full_image_fallback: bool = True):
        self.loader = loader
        self.detector = detector
        self.roi_builder = roi_builder
        self.rectifier = rectifier
        self.reader = reader
        self.full_image_fallback = full_image_fallback

    @classmethod
    def from_settings(cls, settings: Settings) -> "OcrEngine":
        """Crea il motore e tutti i suoi componenti dalla configurazione YAML."""
        roi = settings.section("roi")
        recognition = settings.section("recognition")
        model = OcrModel(**settings.section("model"))      # caricato una volta, usato ai passi 1 e 4
        return cls(
            loader      = ImageLoader(extensions=settings.section("input")["extensions"]),
            detector    = TextDetector(model, **settings.section("tiling")),
            roi_builder = RoiBuilder(
                grouping_distance = roi["grouping_distance"],
                max_rois          = roi["max_rois"],
            ),
            rectifier   = RoiRectifier(
                direction_tolerance_deg = roi["direction_tolerance_deg"],
                min_line_aspect_ratio   = roi["min_line_aspect_ratio"],
                target_text_height      = roi["target_text_height"],
                max_scale               = roi["max_scale"],
                padding_text_heights    = roi["padding_text_heights"],
                max_output_side         = roi["max_output_side"],
            ),
            reader      = TextReader(
                model,
                preprocessing   = recognition["preprocessing"],
                try_upside_down = recognition["try_upside_down"],
            ),
            full_image_fallback = recognition["full_image_fallback"],
        )

    def process_file(self, path: str | Path) -> ImageResult:
        """Elabora una foto da disco. Un errore non solleva eccezioni: viene
        riportato in `ImageResult.error`, così il chiamante riceve sempre una risposta."""
        try:
            image = self.loader.load(Path(path))
        except Exception as error:  # noqa: BLE001
            logger.error("Impossibile leggere %s: %s", path, error)
            return ImageResult(image=InputImage(Path(path)), error=str(error))
        return self.process(image)

    def process_array(self, pixels: np.ndarray, name: str = "image") -> ImageResult:
        """Elabora una foto già in memoria (BGR, convenzione OpenCV)."""
        return self.process(InputImage(path=Path(name), pixels=pixels))

    def process(self, image: InputImage) -> ImageResult:
        """Esegue i 4 passi su una foto."""
        result = ImageResult(image=image)
        try:
            start = time.perf_counter()
            result.text_boxes = self.detector.detect(image.pixels)
            result.rois = self.roi_builder.build(result.text_boxes)
            if not result.rois and self.full_image_fallback:
                result.rois = [RegionOfInterest.whole_image(image.pixels.shape)]
            result.timings["detection"] = time.perf_counter() - start

            start = time.perf_counter()
            for roi in result.rois:
                self.rectifier.rectify(image.pixels, roi)
                self._read(roi)
            result.timings["reading"] = time.perf_counter() - start
        except Exception as error:  # noqa: BLE001 - il chiamante riceve sempre una risposta
            logger.exception("Errore su %s", image.name)
            result.error = str(error)
        return result

    def _read(self, roi: RegionOfInterest) -> None:
        """Legge la ROI raddrizzata e salva i testi (con coordinate sulla foto)."""
        raw_texts, roi.rotation, prepared = self.reader.read(roi.image)
        # Si conserva solo se diversa dalla ROI (preprocessing clahe o otsu).
        roi.prepared_image = None if prepared is roi.image else prepared
        roi.texts = [RecognizedText(text, score, polygon, roi.to_original(polygon))
                     for polygon, text, score in raw_texts]
