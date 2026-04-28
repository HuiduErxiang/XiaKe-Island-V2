"""DOCX parser: extract paragraphs with heading hierarchy."""

import logging
import os
from pathlib import Path

from ..schema import MaterialFormat, ParsedMaterial, ParseError
from ..utils.image_extract import extract_images_from_docx_paragraph
from .. import config

logger = logging.getLogger(__name__)

HEADING_MAP = {0: "#", 1: "##", 2: "###", 3: "####"}


def parse_docx(path: Path, output_dir: Path) -> ParsedMaterial:
    """Parse a DOCX file into heading-preserving Markdown.

    Args:
        path: Path to the DOCX file.
        output_dir: Output directory for extracted assets.

    Returns:
        ParsedMaterial with Markdown content.
    """
    from docx import Document

    filename = os.path.basename(str(path))

    file_size = os.path.getsize(str(path))
    if file_size > config.MAX_FILE_SIZE_BYTES:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.DOCX,
            content="",
            error=ParseError(filename=filename, reason="file_too_large"),
        )

    try:
        doc = Document(str(path))
    except Exception as e:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.DOCX,
            content="",
            error=ParseError(filename=filename, reason="parse_error"),
        )

    blocks: list[str] = []
    paragraph_count = 0

    for para in doc.paragraphs:
        text = para.text.strip()
        if not text:
            continue
        paragraph_count += 1

        if para.style.name.startswith("Heading"):
            # Extract heading level
            try:
                level_str = para.style.name.split()[-1]
                level = int(level_str) - 1  # Heading 1 → level 0
            except (ValueError, IndexError):
                level = 0
            prefix = HEADING_MAP.get(level, "#")
            blocks.append(f"\n{prefix} {text}\n")
        else:
            blocks.append(f"{text}\n")

    # Extract images
    images = extract_images_from_docx_paragraph(doc, output_dir / "assets", filename)

    return ParsedMaterial(
        filename=filename,
        format=MaterialFormat.DOCX,
        content="\n".join(blocks),
        page_count=paragraph_count,
        images=images,
    )
