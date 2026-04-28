"""Tests for PPTX parser."""

import pytest
from input_structure.parsers.pptx_parser import parse_pptx


def test_pptx_slide_count(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_presentation.pptx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pptx(path, output_dir)
    assert result.page_count == 5
    assert result.error is None


def test_pptx_slide_formatting(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_presentation.pptx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pptx(path, output_dir)
    for i in range(1, 6):
        assert f"### Slide {i} —" in result.content


def test_pptx_body_content(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_presentation.pptx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pptx(path, output_dir)
    assert "Key point" in result.content
    assert "Feature A" in result.content


def test_pptx_notes(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_presentation.pptx"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_pptx(path, output_dir)
    assert "Speaker notes" in result.content
    assert "备注" in result.content
