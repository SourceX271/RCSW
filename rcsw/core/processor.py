from __future__ import annotations

import io

import fitz
from PIL import Image

from .models import ScaleMode
from .logger import get_logger

_log = get_logger("processor")


def scale_image(
    pil_img: Image.Image,
    page_w: float,
    page_h: float,
    target_dpi: int,
    mode: ScaleMode,
) -> Image.Image:
    img_w, img_h = pil_img.size
    if img_w <= 0 or img_h <= 0:
        return pil_img
    if page_w <= 0 or page_h <= 0:
        return pil_img

    if target_dpi == 0:
        target_px_w = img_w
        target_px_h = img_h
    else:
        scale = target_dpi / 72.0
        target_px_w = int(page_w * scale)
        target_px_h = int(page_h * scale)

    if mode == ScaleMode.STRETCH:
        scaled_w = target_px_w
        scaled_h = target_px_h
    elif mode == ScaleMode.FIT_WIDTH:
        scaled_w = target_px_w
        scaled_h = int(img_h * (target_px_w / img_w))
    elif mode == ScaleMode.FIT_HEIGHT:
        scaled_h = target_px_h
        scaled_w = int(img_w * (target_px_h / img_h))
    elif mode in (ScaleMode.FILL_CROP, ScaleMode.FIT):
        target_aspect = target_px_w / target_px_h if target_px_h > 0 else 1.0
        img_aspect = img_w / img_h
        if mode == ScaleMode.FILL_CROP:
            if img_aspect > target_aspect:
                scaled_h = target_px_h
                scaled_w = int(img_w * (target_px_h / img_h))
            else:
                scaled_w = target_px_w
                scaled_h = int(img_h * (target_px_w / img_w))
        else:
            if img_aspect > target_aspect:
                scaled_w = target_px_w
                scaled_h = int(img_h * (target_px_w / img_w))
            else:
                scaled_h = target_px_h
                scaled_w = int(img_w * (target_px_h / img_h))
    else:
        return pil_img

    if pil_img.mode == "P":
        pil_img = pil_img.convert("RGBA")
    pil_img = pil_img.resize((scaled_w, scaled_h), Image.LANCZOS)

    if mode == ScaleMode.FILL_CROP:
        crop_x = max(0, (scaled_w - target_px_w) // 2)
        crop_y = max(0, (scaled_h - target_px_h) // 2)
        if crop_x > 0 or crop_y > 0:
            pil_img = pil_img.crop(
                (crop_x, crop_y, crop_x + target_px_w, crop_y + target_px_h)
            )
    elif mode == ScaleMode.FIT_WIDTH:
        if scaled_h > target_px_h:
            crop_y = (scaled_h - target_px_h) // 2
            pil_img = pil_img.crop((0, crop_y, target_px_w, crop_y + target_px_h))
        elif scaled_h < target_px_h:
            canvas = Image.new("RGB", (target_px_w, target_px_h), (255, 255, 255))
            y = (target_px_h - scaled_h) // 2
            canvas.paste(pil_img, (0, y))
            pil_img = canvas
    elif mode == ScaleMode.FIT_HEIGHT:
        if scaled_w > target_px_w:
            crop_x = (scaled_w - target_px_w) // 2
            pil_img = pil_img.crop((crop_x, 0, crop_x + target_px_w, scaled_h))
        elif scaled_w < target_px_w:
            canvas = Image.new("RGB", (target_px_w, target_px_h), (255, 255, 255))
            x = (target_px_w - scaled_w) // 2
            canvas.paste(pil_img, (x, 0))
            pil_img = canvas

    if mode == ScaleMode.FIT and (pil_img.size[0] != target_px_w or pil_img.size[1] != target_px_h):
        canvas = Image.new("RGB", (target_px_w, target_px_h), (255, 255, 255))
        x = (target_px_w - pil_img.size[0]) // 2
        y = (target_px_h - pil_img.size[1]) // 2
        canvas.paste(pil_img, (x, y))
        pil_img = canvas

    return pil_img


def to_rgb(pil_img: Image.Image) -> Image.Image:
    if pil_img.mode in ("RGBA", "LA"):
        background = Image.new("RGB", pil_img.size, (255, 255, 255))
        background.paste(pil_img, mask=pil_img.split()[-1])
        return background
    if pil_img.mode == "P":
        pil_img = pil_img.convert("RGBA")
        background = Image.new("RGB", pil_img.size, (255, 255, 255))
        background.paste(pil_img, mask=pil_img.split()[-1])
        return background
    if pil_img.mode == "CMYK":
        pil_img = pil_img.convert("RGB")
        return pil_img
    if pil_img.mode != "RGB":
        return pil_img.convert("RGB")
    return pil_img


def process_page(
    page: fitz.Page,
    watermark_indices: set[int],
    page_w: float,
    page_h: float,
    dpi: int,
    jpeg_quality: int,
    scale_mode: ScaleMode,
    doc: fitz.Document,
    cached_imgs: list[tuple] | None = None,
) -> bytes | None:
    imgs = cached_imgs if cached_imgs is not None else page.get_images(full=True)
    main_img_info = None
    main_img_size = 0

    for idx, img in enumerate(imgs):
        if idx in watermark_indices:
            continue
        w, h = img[2], img[3]
        area = w * h
        if area > main_img_size:
            main_img_size = area
            main_img_info = img

    if main_img_info is None:
        _log.debug("未找到主图片 (page %d)", page.number)
        return None

    img_data = doc.extract_image(main_img_info[0])
    img_bytes = img_data["image"]

    if dpi == 0:
        return img_bytes

    pil_img = Image.open(io.BytesIO(img_bytes))
    pil_img = scale_image(pil_img, page_w, page_h, dpi, scale_mode)
    pil_img = to_rgb(pil_img)

    buf = io.BytesIO()
    pil_img.save(buf, format="JPEG", quality=jpeg_quality)
    return buf.getvalue()
