"""Configuration for the input-structure Skill."""

# OCR settings
OCR_ENABLED = True
OCR_TIMEOUT_SECONDS = 30  # per-page timeout
OCR_CONFIDENCE_THRESHOLD = 0.60  # below this, emit low-quality warning

# File size limits
MAX_FILE_SIZE_MB = 50
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Image extraction
IMAGE_MIN_DIMENSION_PX = 100  # skip images smaller than this (thumbnails, icons)
IMAGE_FORMAT = "PNG"
MAX_INLINE_IMAGES = 20  # when doc has >50 images, only inline first N

# Encoding fallback
DEFAULT_ENCODING = "utf-8"
