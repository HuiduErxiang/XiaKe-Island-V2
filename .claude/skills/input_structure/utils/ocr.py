"""PaddleOCR wrapper for the input-structure Skill."""

import logging
import time
from pathlib import Path
from typing import Optional

from .. import config

logger = logging.getLogger(__name__)


class OCREngine:
    """Thin wrapper around PaddleOCR for page-level text recognition."""

    def __init__(self, timeout: int = config.OCR_TIMEOUT_SECONDS):
        self._ocr = None
        self._timeout = timeout

    @property
    def ocr(self):
        if self._ocr is None:
            from paddleocr import PaddleOCR
            self._ocr = PaddleOCR(lang="ch", use_angle_cls=True)
        return self._ocr

    def recognize_page(self, image_path: Path) -> tuple[str, float]:
        """OCR a single page image. Returns (text, confidence).

        Raises TimeoutError if the operation exceeds the per-page timeout.
        """
        start = time.monotonic()
        try:
            result = self.ocr.ocr(str(image_path), cls=True)
            elapsed = time.monotonic() - start

            if elapsed > self._timeout:
                raise TimeoutError(f"OCR timeout: {elapsed:.1f}s > {self._timeout}s")

            if not result or not result[0]:
                return "", 0.0

            lines = []
            confidences = []
            for line_info in result[0]:
                text = line_info[1][0]
                conf = line_info[1][1]
                if text and text.strip():
                    lines.append(text.strip())
                    confidences.append(conf)

            avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0
            return "\n".join(lines), avg_confidence

        except TimeoutError:
            raise
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            raise


# Module-level singleton (lazy init on first call)
_engine: Optional[OCREngine] = None


def get_engine() -> OCREngine:
    global _engine
    if _engine is None:
        _engine = OCREngine()
    return _engine


def recognize_page(image_path: Path) -> tuple[str, float]:
    """Convenience function: OCR a page, return (text, confidence)."""
    return get_engine().recognize_page(image_path)
