"""TXT parser: encoding detection and paragraph splitting."""

import logging
import os
from pathlib import Path

import chardet

from ..schema import MaterialFormat, ParsedMaterial, ParseError
from .. import config

logger = logging.getLogger(__name__)


def parse_txt(path: Path) -> ParsedMaterial:
    """Parse a TXT file with encoding detection.

    Args:
        path: Path to the TXT file.

    Returns:
        ParsedMaterial with paragraph-split content.
    """
    filename = os.path.basename(str(path))

    # Check file existence
    if not path.exists():
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.TXT,
            content=f"[{filename} — 文件未找到]",
            error=ParseError(filename=filename, reason="file_not_found"),
        )

    # Check empty file
    file_size = os.path.getsize(str(path))
    if file_size == 0:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.TXT,
            content=f"[{filename} — 空文件]",
            error=ParseError(filename=filename, reason="empty_file"),
        )

    if file_size > config.MAX_FILE_SIZE_BYTES:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.TXT,
            content="",
            error=ParseError(filename=filename, reason="file_too_large"),
        )

    # Detect encoding
    with open(path, "rb") as f:
        raw = f.read()
    detected = chardet.detect(raw)
    encoding = detected.get("encoding") or config.DEFAULT_ENCODING

    try:
        text = raw.decode(encoding)
    except (UnicodeDecodeError, LookupError):
        # Fallback to UTF-8
        try:
            text = raw.decode(config.DEFAULT_ENCODING)
        except UnicodeDecodeError:
            text = raw.decode("latin-1")

    # Split into paragraphs on double newlines
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if not paragraphs:
        # No blank lines — keep raw text
        content = text.strip()
        paragraph_count = 1
    else:
        content = "\n\n".join(paragraphs)
        paragraph_count = len(paragraphs)

    return ParsedMaterial(
        filename=filename,
        format=MaterialFormat.TXT,
        content=content,
        page_count=paragraph_count,
    )
