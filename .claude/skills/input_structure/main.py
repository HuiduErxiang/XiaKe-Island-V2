"""Main entry point for the input-structure Skill."""

import logging
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from .schema import StructuredInput, ParsedMaterial, MaterialFormat, ParseError
from .utils.markdown_builder import build_markdown
from . import config

logger = logging.getLogger(__name__)

PARSER_MAP = {
    ".pdf": "parsers.pdf_parser.parse_pdf",
    ".pptx": "parsers.pptx_parser.parse_pptx",
    ".docx": "parsers.docx_parser.parse_docx",
    ".txt": "parsers.txt_parser.parse_txt",
}


def structure(
    input_text: str,
    file_paths: list[str],
    output_dir: str,
    ocr_enabled: bool = True,
    ocr_timeout: int = 30,
) -> StructuredInput:
    """Convert user-supplied materials into structured Markdown.

    Args:
        input_text: The user's original writing request.
        file_paths: List of file paths to parse (can be empty).
        output_dir: Directory where output files will be written.
        ocr_enabled: Whether to use OCR for scanned PDF pages.
        ocr_timeout: Per-page OCR timeout in seconds.

    Returns:
        StructuredInput containing the results.
    """
    config.OCR_TIMEOUT_SECONDS = ocr_timeout

    out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = out_dir / "assets"
    assets_dir.mkdir(exist_ok=True)

    # Deduplicate file paths (per spec edge case)
    seen = set()
    unique_paths = []
    for fp in file_paths:
        resolved = str(Path(fp).resolve())
        if resolved not in seen:
            seen.add(resolved)
            unique_paths.append(fp)

    materials: list[ParsedMaterial] = []

    for fp in unique_paths:
        path = Path(fp)

        if not path.exists():
            materials.append(ParsedMaterial(
                filename=os.path.basename(fp),
                format=MaterialFormat.TXT,
                content="",
                error=ParseError(filename=os.path.basename(fp), reason="file_not_found"),
            ))
            continue

        ext = path.suffix.lower()
        material = _parse_file(path, ext, out_dir, ocr_enabled)
        materials.append(material)

    # Build markdown
    md_content = build_markdown(materials, input_text, out_dir)

    # Write output
    md_path = out_dir / "structured_input.md"
    md_path.write_text(md_content, encoding="utf-8")

    return StructuredInput(
        user_request=input_text,
        materials=materials,
        assets_dir=str(assets_dir),
        parsed_at=datetime.now(),
    )


def _parse_file(
    path: Path,
    ext: str,
    output_dir: Path,
    ocr_enabled: bool,
) -> ParsedMaterial:
    """Route file to correct parser by extension."""
    filename = os.path.basename(str(path))

    if ext == ".pdf":
        from .parsers.pdf_parser import parse_pdf
        return parse_pdf(path, output_dir, ocr_enabled=ocr_enabled)
    elif ext == ".pptx":
        from .parsers.pptx_parser import parse_pptx
        return parse_pptx(path, output_dir)
    elif ext == ".docx":
        from .parsers.docx_parser import parse_docx
        return parse_docx(path, output_dir)
    elif ext == ".txt":
        from .parsers.txt_parser import parse_txt
        return parse_txt(path)
    else:
        return ParsedMaterial(
            filename=filename,
            format=MaterialFormat.TXT,
            content=f"[{filename} — 不支持的格式：{ext}]",
            error=ParseError(filename=filename, reason="unsupported_format"),
        )
