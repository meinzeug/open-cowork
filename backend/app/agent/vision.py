import base64
import io
from typing import Any, Dict, Tuple

from PIL import Image


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
