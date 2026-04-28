"""Tests for DOCX parser."""

import pytest
from input_structure.parsers.docx_parser import parse_docx


def test_docx_heading_hierarchy(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_report.docx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_docx(path, output_dir)
    assert result.error is None
    assert "# Clinical Research Report" in result.content
    assert "## Background" in result.content
    assert "## Methods" in result.content
    assert "## Results" in result.content
    assert "### Participant Selection" in result.content
    assert "### Statistical Analysis" in result.content


def test_docx_paragraph_content(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_report.docx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_docx(path, output_dir)
    assert "Alzheimer" in result.content
    assert "placebo-controlled" in result.content


def test_docx_paragraph_count(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_report.docx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_docx(path, output_dir)
    assert result.page_count > 0
