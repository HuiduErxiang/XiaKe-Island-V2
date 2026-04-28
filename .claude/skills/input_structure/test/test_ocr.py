"""Tests for OCR engine with mocked PaddleOCR."""
import sys
from unittest import mock
import pytest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from input_structure.utils.ocr import OCREngine, get_engine, recognize_page


@pytest.fixture(autouse=True)
def reset_ocr_singleton():
    import input_structure.utils.ocr as ocr_module
    ocr_module._engine = None


def test_ocr_engine_lazy_init():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        engine = OCREngine()
        assert engine._ocr is None
        # Trigger lazy init
        mock_paddle = sys.modules["paddleocr"]
        engine.ocr  # access property to trigger init
        mock_paddle.PaddleOCR.assert_called_once_with(lang="ch", use_angle_cls=True)


def test_recognize_page_success():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        engine = OCREngine()

        mock_paddle = sys.modules["paddleocr"]
        mock_instance = mock.MagicMock()
        mock_instance.ocr.return_value = [[
            [None, ("Hello world", 0.95)],
            [None, ("  ", 0.50)],
            [None, ("Test line", 0.88)],
        ]]
        mock_paddle.PaddleOCR.return_value = mock_instance
        engine._ocr = mock_instance

        text, conf = engine.recognize_page(Path("/tmp/test.png"))

        assert "Hello world" in text
        assert "Test line" in text
        assert "  " not in text  # blank lines excluded
        assert conf == pytest.approx((0.95 + 0.88) / 2, rel=0.01)


def test_recognize_page_empty_result():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        engine = OCREngine()

        mock_instance = mock.MagicMock()
        mock_instance.ocr.return_value = []
        engine._ocr = mock_instance

        text, conf = engine.recognize_page(Path("/tmp/test.png"))
        assert text == ""
        assert conf == 0.0


def test_recognize_page_none_result():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        engine = OCREngine()

        mock_instance = mock.MagicMock()
        mock_instance.ocr.return_value = None
        engine._ocr = mock_instance

        text, conf = engine.recognize_page(Path("/tmp/test.png"))
        assert text == ""
        assert conf == 0.0


def test_ocr_singleton():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        e1 = get_engine()
        e2 = get_engine()
        assert e1 is e2


def test_recognize_page_convenience():
    with mock.patch.dict(sys.modules, {"paddleocr": mock.MagicMock()}):
        import input_structure.utils.ocr as ocr_module
        ocr_module._engine = None

        mock_paddle = sys.modules["paddleocr"]
        mock_instance = mock.MagicMock()
        mock_instance.ocr.return_value = [[
            [None, ("OCR text", 0.82)],
        ]]
        mock_paddle.PaddleOCR.return_value = mock_instance

        text, conf = recognize_page(Path("/tmp/test.png"))
        assert "OCR text" in text
        assert conf == 0.82
