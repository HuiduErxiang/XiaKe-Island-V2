"""Tests for PDF parser: text, tables, charts, OCR annotations."""

import re
import pytest
from input_structure.parsers.pdf_parser import parse_pdf


def test_text_pdf_page_count(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pdf(path, output_dir)
    assert result.page_count == 3
    assert result.error is None


def test_text_pdf_content_structure(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pdf(path, output_dir)
    assert "### 第1页" in result.content
    assert "### 第2页" in result.content
    assert "### 第3页" in result.content
    assert "Introduction to Lecanemab" in result.content


def test_table_pdf_conversion(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_table.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pdf(path, output_dir)
    assert result.page_count == 2
    assert "CDR-SB" in result.content
    assert "---" in result.content


def test_chart_pdf_image_extraction(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_chart.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pdf(path, output_dir)
    assert result.page_count == 2
    assert len(result.images) >= 1
    for img in result.images:
        assert img.path.startswith("assets/")
        assert img.path.endswith(".png")


def test_missing_file(fixtures_dir, output_dir):
    path = fixtures_dir / "nonexistent.pdf"
    result = parse_pdf(path, output_dir)
    assert result.error is not None


def test_page_numbering(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pdf(path, output_dir)
    page_headers = re.findall(r"### 第(\d+)页", result.content)
    assert page_headers == ["1", "2", "3"]
