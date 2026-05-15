import logging
import numpy as np
from rapidocr_onnxruntime import RapidOCR

logger = logging.getLogger(__name__)

_ocr_reader = None


def get_ocr_reader() -> RapidOCR:
    global _ocr_reader
    if _ocr_reader is None:
        logger.info("Loading RapidOCR reader")
        _ocr_reader = RapidOCR()
    return _ocr_reader


def ocr_page_image(pil_image) -> str:
    """Run OCR on a PIL image of a PDF page, return recognized text."""
    reader = get_ocr_reader()
    arr = np.array(pil_image)
    result, _ = reader(arr)
    if not result:
        return ""
    texts = [line[1] for line in result if line[2] > 0.5]
    return "\n".join(texts)
