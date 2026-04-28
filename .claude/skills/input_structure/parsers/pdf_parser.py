"""PDF parser: text extraction with OCR fallback, table detection, image extraction."""

import logging
import os
import re
import time
from pathlib import Path
from typing import Optional

import fitz  # PyMuPDF

from ..schema import MaterialFormat, ParsedMaterial, ParsedImage, ParseError
from ..utils.image_extract import extract_images_from_pdf
from .. import config

logger = logging.getLogger(__name__)


def parse_pdf(path: Path, output_dir: Path, ocr_enabled: bool = True) -> ParsedMaterial:
    """Parse a PDF file into structured Markdown.

    Args:
        path: Path to the PDF file.
        output_dir: Output directory for extracted assets.
        ocr_enabled: Whether to attempt OCR on pages with no text.

    Returns:
        ParsedMaterial with structured Markdown content.
    """
    filename = os.path.basename(str(path))

    # Check file existence
    if not path.exists():
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.PDF,
            content=f"[{filename} — 文件未找到]",
            error=ParseError(filename=filename, reason="file_not_found"),
        )

    # Check file size
    file_size = os.path.getsize(str(path))
    if file_size > config.MAX_FILE_SIZE_BYTES:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.PDF,
            content="",
            page_count=0,
            error=ParseError(filename=filename, reason="file_too_large"),
        )

    try:
        doc = fitz.open(str(path))
    except Exception:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.PDF,
            content="",
            page_count=0,
            error=ParseError(filename=filename, reason="parse_error"),
        )

    # Check for encryption
    if doc.is_encrypted:
        doc.close()
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.PDF,
            content="",
            page_count=0,
            error=ParseError(filename=filename, reason="encrypted_pdf"),
        )

    all_images: list[ParsedImage] = []
    markdown_blocks: list[str] = []
    page_count = doc.page_count

    for page_num in range(page_count):
        try:
            page = doc.load_page(page_num)
            page_text = page.get_text("text").strip()

            block: Optional[str] = None

            if page_text:
                # Has text layer — extract directly
                block = _process_text_page(page_text, page_num)
            elif ocr_enabled:
                # No text layer — try OCR
                block = _process_scanned_page(page, page_num, output_dir)
            else:
                block = f"### 第{page_num + 1}页\n\n[第{page_num + 1}页 — 无可提取文本，OCR 已禁用]\n"

            markdown_blocks.append(block)

            # Extract images
            page_images = extract_images_from_pdf(
                page, output_dir / "assets", filename, page_num + 1
            )
            all_images.extend(page_images)

            # Append figure references after the page text
            for img in page_images:
                caption = img.caption or f"图{img.index}"
                block += f"\n\n![{caption}]({img.path})\n"

        except TimeoutError:
            markdown_blocks.append(f"### 第{page_num + 1}页\n\n[第{page_num + 1}页 — OCR 超时]\n")
        except Exception as e:
            logger.error(f"Error processing page {page_num + 1} of {filename}: {e}")
            markdown_blocks.append(f"### 第{page_num + 1}页\n\n[第{page_num + 1}页 — 解析错误]\n")

    doc.close()

    full_markdown = "\n\n".join(markdown_blocks)
    return ParsedMaterial(
        filename=filename,
        format=MaterialFormat.PDF,
        content=full_markdown,
        page_count=page_count,
        images=all_images,
    )


def _process_text_page(text: str, page_num: int) -> str:
    """Process a page with extractable text."""
    lines = text.split("\n")
    cleaned: list[str] = [f"### 第{page_num + 1}页\n"]

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        # Detect potential headings: all-caps, short lines ending without punctuation
        if _looks_like_heading(stripped, lines):
            cleaned.append(f"\n## {stripped}\n")
        else:
            cleaned.append(f"{stripped}\n")

    # Detect tables in the text
    result = "\n".join(cleaned)
    result = _detect_and_format_tables(result)
    return result


def _process_scanned_page(page, page_num: int, output_dir: Path) -> str:
    """OCR a scanned page and annotate result."""
    from ..utils.ocr import recognize_page

    # Render page to image for OCR
    pix = page.get_pixmap(dpi=200)
    img_path = output_dir / "_ocr_temp.png"
    pix.save(str(img_path))

    text, confidence = recognize_page(img_path)

    # Clean up temp
    try:
        os.remove(str(img_path))
    except OSError:
        pass

    header = f"### 第{page_num + 1}页 — OCR 识别\n"

    if confidence < config.OCR_CONFIDENCE_THRESHOLD:
        header += f"\n[第{page_num + 1}页 — OCR 识别质量低]\n"

    return header + "\n" + (text or f"[第{page_num + 1}页 — 无可识别文本]")


def _looks_like_heading(line: str, all_lines: list[str]) -> bool:
    """Heuristic: detect if a line looks like a section heading."""
    # Short line, possibly all caps or title case
    if len(line) > 80:
        return False
    # All uppercase (common in PDFs)
    if line.isupper() and len(line) > 3:
        return True
    # Title Case and short (but not a full sentence)
    words = line.split()
    if len(words) <= 10 and all(w[0].isupper() for w in words if w[0].isalpha()):
        # Not ending with period (headings don't end with period)
        if not line.rstrip().endswith("."):
            return True
    return False


def _detect_and_format_tables(text: str) -> str:
    """Detect tab-separated rows and convert to Markdown tables."""
    lines = text.split("\n")
    result: list[str] = []
    i = 0

    while i < len(lines):
        line = lines[i]
        # Detect tab-separated data (potential table row)
        if "\t" in line and line.count("\t") >= 2:
            table_rows = []
            while i < len(lines) and "\t" in lines[i] and lines[i].count("\t") >= 2:
                table_rows.append(lines[i])
                i += 1

            if table_rows:
                result.append(_rows_to_markdown_table(table_rows))
            continue

        result.append(line)
        i += 1

    return "\n".join(result)


def _rows_to_markdown_table(rows: list[str]) -> str:
    """Convert tab-separated rows to a Markdown table."""
    if not rows:
        return ""

    split_rows = [r.split("\t") for r in rows]
    col_count = max(len(r) for r in split_rows)

    # Normalize to same column count
    normalized = [r + [""] * (col_count - len(r)) for r in split_rows]

    md_rows = ["| " + " | ".join(r) + " |" for r in normalized]

    # Insert header separator after first row
    separator = "|" + "|".join(["---"] * col_count) + "|"
    md_rows.insert(1, separator)

    return "\n".join(md_rows)
