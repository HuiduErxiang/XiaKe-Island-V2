"""Tests for TXT parser."""

import pytest
from input_structure.parsers.txt_parser import parse_txt


def test_txt_utf8_paragraphs(fixtures_dir):
    path = fixtures_dir / "sample_notes.txt"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_txt(path)
    assert result.error is None
    assert "lecanemab" in result.content.lower()
    assert result.page_count >= 3


def test_txt_gbk_encoding(fixtures_dir):
    path = fixtures_dir / "sample_gbk.txt"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_txt(path)
    assert result.error is None
    assert "临床" in result.content


def test_txt_empty_file(fixtures_dir):
    path = fixtures_dir / "empty.txt"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = parse_txt(path)
    assert result.error is not None
    assert "空文件" in result.content


def test_txt_missing_file():
    from pathlib import Path
    path = Path("/tmp/nonexistent_file_12345.txt")
    result = parse_txt(path)
    assert result.error is not None
