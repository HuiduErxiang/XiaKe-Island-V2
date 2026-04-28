"""Markdown assembly: combine parsed materials into the final output."""

from pathlib import Path

from ..schema import ParsedMaterial
from .. import config


def build_markdown(
    materials: list[ParsedMaterial],
    user_request: str,
    output_dir: Path,
) -> str:
    """Assemble the final structured Markdown document.

    Args:
        materials: Ordered list of parsed materials.
        user_request: Original user writing request text.
        output_dir: The output directory (for asset path calculation).

    Returns:
        Complete Markdown string ready to write to file.
    """
    parts: list[str] = []

    # Section 1: User writing request
    parts.append("# 用户写作需求\n")
    parts.append(f"{user_request}\n")
    parts.append("\n---\n")

    # Section 2: Supplementary materials
    parts.append("# 补充材料\n")

    if not materials:
        parts.append("\n无\n")
        return "\n".join(parts)

    for material in materials:
        parts.append(f"\n## {material.filename}\n")

        if material.error:
            reason_label = _error_reason_label(material.error.reason)
            parts.append(f"\n[{material.filename} — {reason_label}]\n")
            continue

        parts.append(f"{material.content}\n")

        # Append figure references
        _append_figure_references(material, parts)

    return "\n".join(parts)


def _append_figure_references(material: ParsedMaterial, parts: list[str]) -> None:
    """Append figure markdown references, limiting inline images per spec."""
    images = material.images
    inline_count = min(len(images), config.MAX_INLINE_IMAGES)

    for img in images[:inline_count]:
        caption = img.caption or f"图片"
        parts.append(f"\n![{caption}]({img.path})\n")

    if len(images) > config.MAX_INLINE_IMAGES:
        parts.append(f"\n> 本文档共提取 {len(images)} 张图片，仅展示前 {config.MAX_INLINE_IMAGES} 张。完整列表：\n")
        for img in images[config.MAX_INLINE_IMAGES:]:
            parts.append(f"- [{img.path}]({img.path})\n")


def _error_reason_label(reason: str) -> str:
    """Map error reason to user-facing label."""
    labels = {
        "unsupported_format": "不支持的格式",
        "file_not_found": "无法读取",
        "encrypted_pdf": "加密PDF，无法解析",
        "file_too_large": "文件过大，跳过解析",
        "empty_file": "空文件",
        "ocr_timeout": "OCR 超时",
        "corrupted_image": "图表无法提取",
        "parse_error": "解析失败",
    }
    return labels.get(reason, reason)
