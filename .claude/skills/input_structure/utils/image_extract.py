"""Image extraction from PDF/PPTX/DOCX documents."""

import io
import logging
from pathlib import Path
from typing import Optional

from PIL import Image

from ..schema import ParsedImage
from .. import config

logger = logging.getLogger(__name__)


def extract_images_from_pdf(
    page,
    output_dir: Path,
    source_filename: str,
    page_num: int,
) -> list[ParsedImage]:
    """Extract embedded images from a PyMuPDF page.

    Args:
        page: PyMuPDF Page object.
        output_dir: Directory to save extracted PNGs.
        source_filename: Original file name (for naming).
        page_num: 1-based page number.

    Returns:
        List of ParsedImage records.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    images = []

    image_list = page.get_images(full=True)
    for idx, img_info in enumerate(image_list, start=1):
        xref = img_info[0]
        try:
            base_image = page.parent.extract_image(xref)
            if not base_image:
                continue

            img_bytes = base_image["image"]
            img_ext = base_image["ext"]

            # Skip tiny images (thumbnails, icons)
            pil_img = Image.open(io.BytesIO(img_bytes))
            if pil_img.width < config.IMAGE_MIN_DIMENSION_PX or pil_img.height < config.IMAGE_MIN_DIMENSION_PX:
                continue

            # Convert to PNG
            stem = Path(source_filename).stem
            safe_name = f"{stem}_p{page_num}_fig{idx}.png"
            img_path = output_dir / safe_name
            pil_img.save(str(img_path), format="PNG")

            images.append(ParsedImage(
                source_file=source_filename,
                page=page_num,
                index=idx,
                path=f"assets/{safe_name}",
                width=pil_img.width,
                height=pil_img.height,
            ))
        except Exception as e:
            logger.warning(f"Failed to extract image {idx} from page {page_num}: {e}")

    return images


def extract_images_from_pptx(
    slide,
    output_dir: Path,
    source_filename: str,
    slide_num: int,
) -> list[ParsedImage]:
    """Extract images from a PPTX slide's shapes.

    Args:
        slide: python-pptx Slide object.
        output_dir: Directory to save extracted PNGs.
        source_filename: Original file name.
        slide_num: 1-based slide number.

    Returns:
        List of ParsedImage records.
    """
    from pptx.enum.shapes import MSO_SHAPE_TYPE

    output_dir.mkdir(parents=True, exist_ok=True)
    images = []
    idx = 0

    for shape in slide.shapes:
        if shape.shape_type == MSO_SHAPE_TYPE.PICTURE:
            idx += 1
            try:
                image = shape.image
                img_bytes = image.blob
                pil_img = Image.open(io.BytesIO(img_bytes))

                if pil_img.width < config.IMAGE_MIN_DIMENSION_PX:
                    continue

                stem = Path(source_filename).stem
                safe_name = f"{stem}_slide{slide_num}_img{idx}.png"
                img_path = output_dir / safe_name
                pil_img.save(str(img_path), format="PNG")

                # Use alt text as caption if available
                caption = shape.alt_text if hasattr(shape, 'alt_text') else ""

                images.append(ParsedImage(
                    source_file=source_filename,
                    page=slide_num,
                    index=idx,
                    path=f"assets/{safe_name}",
                    caption=caption,
                    width=pil_img.width,
                    height=pil_img.height,
                ))
            except Exception as e:
                logger.warning(f"Failed to extract image from slide {slide_num}: {e}")

    return images


def extract_images_from_docx_paragraph(
    doc,
    output_dir: Path,
    source_filename: str,
) -> list[ParsedImage]:
    """Extract inline images from a DOCX document.

    Args:
        doc: python-docx Document object.
        output_dir: Directory to save extracted PNGs.
        source_filename: Original file name.

    Returns:
        List of ParsedImage records.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    images = []
    idx = 0

    for rel in doc.part.rels.values():
        if "image" in rel.reltype:
            idx += 1
            try:
                img_bytes = rel.target_part.blob
                pil_img = Image.open(io.BytesIO(img_bytes))

                if pil_img.width < config.IMAGE_MIN_DIMENSION_PX:
                    continue

                stem = Path(source_filename).stem
                safe_name = f"{stem}_img{idx}.png"
                img_path = output_dir / safe_name
                pil_img.save(str(img_path), format="PNG")

                images.append(ParsedImage(
                    source_file=source_filename,
                    page=0,
                    index=idx,
                    path=f"assets/{safe_name}",
                    width=pil_img.width,
                    height=pil_img.height,
                ))
            except Exception as e:
                logger.warning(f"Failed to extract DOCX image {idx}: {e}")

    return images
