"""Integration tests: mixed formats, failure isolation, image limits, edge cases."""

import os
import time
import pytest
from input_structure.main import structure


def test_mixed_format_ordering(fixtures_dir, output_dir):
    paths = [
        str(fixtures_dir / "sample_text.pdf"),
        str(fixtures_dir / "sample_presentation.pptx"),
        str(fixtures_dir / "sample_notes.txt"),
    ]
    missing = [p for p in paths if not os.path.exists(p)]
    if missing:
        pytest.skip(f"Missing fixtures: {missing}")

    result = structure(
        input_text="综合分析材料",
        file_paths=paths,
        output_dir=str(output_dir),
    )

    assert len(result.materials) == 3
    for m in result.materials:
        assert m.error is None, f"Unexpected error in {m.filename}: {m.error}"

    md_path = output_dir / "structured_input.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "sample_text.pdf" in content
    assert "sample_presentation.pptx" in content
    assert "sample_notes.txt" in content


def test_failure_isolation(fixtures_dir, output_dir):
    paths = [
        str(fixtures_dir / "sample_notes.txt"),
        str(fixtures_dir / "nonexistent.pdf"),
        str(fixtures_dir / "empty.txt"),
    ]
    exists = [p for p in paths if os.path.exists(p)]
    if len(exists) < 2:
        pytest.skip("Need more fixtures")

    result = structure(
        input_text="部分文件缺失测试",
        file_paths=paths,
        output_dir=str(output_dir),
    )

    errors = [m for m in result.materials if m.error]
    successes = [m for m in result.materials if not m.error]
    assert len(errors) >= 1
    assert len(successes) >= 1


def test_output_file_structure(fixtures_dir, output_dir):
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")

    result = structure(
        input_text="写一篇关于仑卡奈单抗的科普文章",
        file_paths=[str(path)],
        output_dir=str(output_dir),
    )

    md_path = output_dir / "structured_input.md"
    assert md_path.exists()
    content = md_path.read_text(encoding="utf-8")
    assert "# 用户写作需求" in content
    assert "# 补充材料" in content
    assert "仑卡奈单抗" in content


def test_timing_budget_text_pdf(fixtures_dir, output_dir):
    """SC-001: text PDF ≤5s."""
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")

    start = time.perf_counter()
    result = structure(
        input_text="性能测试",
        file_paths=[str(path)],
        output_dir=str(output_dir),
    )
    elapsed = time.perf_counter() - start

    assert result.materials[0].error is None
    assert elapsed < 5.0, f"Text PDF parse took {elapsed:.2f}s, exceeding 5s budget"


def test_timing_budget_pptx(fixtures_dir, output_dir):
    """SC-002: PPTX ≤3s."""
    path = fixtures_dir / "sample_presentation.pptx"
    if not path.exists():
        pytest.skip("Fixture not found")

    start = time.perf_counter()
    result = structure(
        input_text="性能测试",
        file_paths=[str(path)],
        output_dir=str(output_dir),
    )
    elapsed = time.perf_counter() - start

    assert result.materials[0].error is None
    assert elapsed < 3.0, f"PPTX parse took {elapsed:.2f}s, exceeding 3s budget"


def test_dedup_duplicate_files(fixtures_dir, output_dir):
    """Edge case: duplicate file paths should only parse once."""
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")

    result = structure(
        input_text="去重测试",
        file_paths=[str(path), str(path), str(path)],
        output_dir=str(output_dir),
    )
    assert len(result.materials) == 1


def test_fr009_no_semantic_processing(fixtures_dir, output_dir):
    """FR-009: output must have no AI-generated summaries or opinions."""
    path = fixtures_dir / "sample_text.pdf"
    if not path.exists():
        pytest.skip("Fixture not found")

    result = structure(
        input_text="总结这篇文献",
        file_paths=[str(path)],
        output_dir=str(output_dir),
    )

    md_path = output_dir / "structured_input.md"
    content = md_path.read_text(encoding="utf-8")
    supp_section = content.split("# 补充材料")[1] if "# 补充材料" in content else ""
    synthesized_markers = ["综上所述", "本文要点", "核心发现", "总结如下"]
    for marker in synthesized_markers:
        assert marker not in supp_section, f"Found synthesized marker '{marker}' in supplementary section"


def test_image_overflow_limit(output_dir):
    """When >MAX_INLINE_IMAGES images, only first N are inlined."""
    from input_structure.schema import ParsedMaterial, ParsedImage, MaterialFormat
    from input_structure.utils.markdown_builder import build_markdown
    from input_structure import config

    images = [
        ParsedImage(source_file="test.pdf", page=1, index=i, path=f"assets/img_{i:03d}.png")
        for i in range(config.MAX_INLINE_IMAGES + 5)
    ]
    material = ParsedMaterial(
        filename="test.pdf",
        format=MaterialFormat.PDF,
        content="Chart data",
        images=images,
    )
    md = build_markdown([material], "test", output_dir)
    assert "仅展示前" in md
    assert f"共提取 {len(images)} 张图片" in md
