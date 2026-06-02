import base64
import io
from typing import Any, Dict, Tuple

from PIL import Image, ImageDraw, ImageFont


def _coerce_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _coerce_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def crop_and_zoom_png(
    screenshot_base64: str,
    params: Dict[str, Any],
    screen_width: int,
    screen_height: int
) -> Tuple[str, Dict[str, Any]]:
    image_bytes = base64.b64decode(screenshot_base64)
    with Image.open(io.BytesIO(image_bytes)) as image:
        source = image.convert("RGB")
        actual_width, actual_height = source.size

        coordinate_width = max(screen_width, 1)
        coordinate_height = max(screen_height, 1)

        x = _coerce_int(params.get("x"), 0)
        y = _coerce_int(params.get("y"), 0)
        width = _coerce_int(params.get("width", params.get("w")), 240)
        height = _coerce_int(params.get("height", params.get("h")), 180)
        scale = _coerce_float(params.get("scale"), 3.0)

        width = max(20, min(width, coordinate_width))
        height = max(20, min(height, coordinate_height))
        scale = max(1.0, min(scale, 6.0))

        left = max(0, min(x, coordinate_width - 1))
        top = max(0, min(y, coordinate_height - 1))
        right = max(left + 1, min(left + width, coordinate_width))
        bottom = max(top + 1, min(top + height, coordinate_height))

        pixel_left = round((left / coordinate_width) * actual_width)
        pixel_top = round((top / coordinate_height) * actual_height)
        pixel_right = round((right / coordinate_width) * actual_width)
        pixel_bottom = round((bottom / coordinate_height) * actual_height)

        crop = source.crop((pixel_left, pixel_top, pixel_right, pixel_bottom))
        zoomed_size = (
            max(1, round(crop.width * scale)),
            max(1, round(crop.height * scale))
        )
        zoomed = crop.resize(zoomed_size, Image.Resampling.LANCZOS)

        output = io.BytesIO()
        zoomed.save(output, format="PNG", optimize=True)

    normalized = {
        "x": left,
        "y": top,
        "width": right - left,
        "height": bottom - top,
        "scale": scale,
        "output_width": zoomed_size[0],
        "output_height": zoomed_size[1],
    }
    return base64.b64encode(output.getvalue()).decode("utf-8"), normalized


def _load_grid_font(font_size: int):
    """Best-effort load of a small TrueType font, falling back to PIL default."""
    for candidate in (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ):
        try:
            return ImageFont.truetype(candidate, font_size)
        except Exception:
            continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def annotate_grid(
    screenshot_base64: str,
    screen_width: int,
    screen_height: int,
    spacing: int = 100,
) -> str:
    """
    Overlay a light coordinate grid with axis labels onto the screenshot.

    The grid is drawn in the LLM coordinate space (``screen_width`` x
    ``screen_height``) so the model can read off accurate click coordinates
    directly from the image. The original screenshot is never mutated; a new
    PNG is returned as base64.
    """
    spacing = max(40, int(spacing))
    image_bytes = base64.b64decode(screenshot_base64)
    with Image.open(io.BytesIO(image_bytes)) as image:
        canvas = image.convert("RGB")
        actual_width, actual_height = canvas.size

        coord_w = max(screen_width, 1)
        coord_h = max(screen_height, 1)
        sx = actual_width / coord_w
        sy = actual_height / coord_h

        overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)
        font = _load_grid_font(max(10, round(11 * min(sx, sy))))

        line_color = (0, 255, 200, 70)
        label_bg = (0, 0, 0, 140)
        label_fg = (0, 255, 200, 230)

        # Vertical lines + x labels
        x = spacing
        while x < coord_w:
            px = round(x * sx)
            draw.line([(px, 0), (px, actual_height)], fill=line_color, width=1)
            label = str(x)
            ty = 2
            draw.rectangle([px + 1, ty, px + 1 + 7 * len(label), ty + 13], fill=label_bg)
            if font:
                draw.text((px + 2, ty), label, fill=label_fg, font=font)
            x += spacing

        # Horizontal lines + y labels
        y = spacing
        while y < coord_h:
            py = round(y * sy)
            draw.line([(0, py), (actual_width, py)], fill=line_color, width=1)
            label = str(y)
            draw.rectangle([1, py + 1, 1 + 7 * len(label), py + 14], fill=label_bg)
            if font:
                draw.text((2, py + 1), label, fill=label_fg, font=font)
            y += spacing

        combined = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")
        output = io.BytesIO()
        combined.save(output, format="PNG", optimize=True)

    return base64.b64encode(output.getvalue()).decode("utf-8")


def compute_change_ratio(
    previous_base64: str,
    current_base64: str,
    luminance_threshold: int = 24,
    sample_size: int = 160,
) -> float:
    """
    Estimate how much the screen changed between two screenshots.

    Both images are downscaled to a small grayscale thumbnail and compared
    pixel-by-pixel. Returns the fraction (0.0–1.0) of sampled pixels whose
    brightness changed by more than ``luminance_threshold``. A value near 0
    means the last action had essentially no visible effect.
    """
    if not previous_base64 or not current_base64:
        return 1.0
    try:
        prev_bytes = base64.b64decode(previous_base64)
        curr_bytes = base64.b64decode(current_base64)
        with Image.open(io.BytesIO(prev_bytes)) as prev_img, \
                Image.open(io.BytesIO(curr_bytes)) as curr_img:
            size = (max(16, sample_size), max(12, round(sample_size * 0.75)))
            prev_small = prev_img.convert("L").resize(size, Image.Resampling.BILINEAR)
            curr_small = curr_img.convert("L").resize(size, Image.Resampling.BILINEAR)
            prev_px = prev_small.load()
            curr_px = curr_small.load()
            changed = 0
            total = size[0] * size[1]
            for yy in range(size[1]):
                for xx in range(size[0]):
                    if abs(prev_px[xx, yy] - curr_px[xx, yy]) > luminance_threshold:
                        changed += 1
            return changed / total if total else 1.0
    except Exception:
        return 1.0
