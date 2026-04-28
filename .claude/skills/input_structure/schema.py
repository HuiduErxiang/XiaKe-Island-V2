"""Data classes for the input-structure Skill."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class MaterialFormat(str, Enum):
    PDF = "pdf"
    PPTX = "pptx"
    DOCX = "docx"
    TXT = "txt"


class ErrorReason:
    UNSUPPORTED_FORMAT = "unsupported_format"
    FILE_NOT_FOUND = "file_not_found"
    ENCRYPTED_PDF = "encrypted_pdf"
    FILE_TOO_LARGE = "file_too_large"
    EMPTY_FILE = "empty_file"
    OCR_TIMEOUT = "ocr_timeout"
    CORRUPTED_IMAGE = "corrupted_image"
    PARSE_ERROR = "parse_error"


@dataclass
class ParsedImage:
    source_file: str
    page: int
    index: int
    path: str
    caption: str = ""
    width: int = 0
    height: int = 0


@dataclass
class ParseError:
    filename: str
    reason: str
    blocks_others: bool = False


@dataclass
class ParsedMaterial:
    filename: str
    format: MaterialFormat
    content: str
    page_count: int = 0
    images: list[ParsedImage] = field(default_factory=list)
    error: Optional[ParseError] = None


@dataclass
class StructuredInput:
    user_request: str
    materials: list[ParsedMaterial]
    assets_dir: Optional[str] = None
    parsed_at: datetime = field(default_factory=datetime.now)
