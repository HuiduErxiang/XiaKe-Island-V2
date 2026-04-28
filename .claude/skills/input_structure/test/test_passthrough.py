"""Tests for US3: pure text passthrough when no files."""

import pytest
from pathlib import Path
from input_structure.main import structure


def test_no_files_returns_valid_markdown(output_dir):
    result = structure(
        input_text="写一篇科普文章",
        file_paths=[],
        output_dir=str(output_dir),
    )
    assert result.materials == []
    assert result.user_request == "写一篇科普文章"
    md_path = output_dir / "structured_input.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "# 用户写作需求" in content
    assert "写一篇科普文章" in content
    assert "无" in content


def test_empty_file_annotation(fixtures_dir, output_dir):
    path = fixtures_dir / "empty.txt"
    if not path.exists():
        pytest.skip("Fixture not found")
    result = structure(
        input_text="test",
        file_paths=[str(path)],
        output_dir=str(output_dir),
    )
    assert len(result.materials) == 1
    m = result.materials[0]
    assert "空文件" in m.content


def test_unsupported_format_skip(output_dir):
    result = structure(
        input_text="test",
        file_paths=["/tmp/fake.xlsx"],
        output_dir=str(output_dir),
    )
    assert len(result.materials) == 1
    m = result.materials[0]
    assert m.error is not None
    assert m.error.reason == "file_not_found"


def test_module_getattr_fallback():
    import input_structure
    with pytest.raises(AttributeError):
        _ = input_structure.nonexistent_attr


def test_unsupported_extension(output_dir, tmp_path):
    fake_file = tmp_path / "data.xyz"
    fake_file.write_text("some data")
    result = structure(
        input_text="test",
        file_paths=[str(fake_file)],
        output_dir=str(output_dir),
    )
    m = result.materials[0]
    assert m.error is not None
    assert m.error.reason == "unsupported_format"
    assert "不支持的格式" in m.content
