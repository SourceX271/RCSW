from __future__ import annotations

import io

import pytest
from PIL import Image
from rcsw.core.processor import scale_image, to_rgb, process_page
from rcsw.core.detector import ScaleMode


class TestToRgb:
    def test_rgb_passthrough(self):
        img = Image.new("RGB", (100, 100), (255, 128, 64))
        result = to_rgb(img)
        assert result.mode == "RGB"
        assert result.size == (100, 100)

    def test_rgba_to_rgb(self):
        img = Image.new("RGBA", (50, 50), (255, 0, 0, 128))
        result = to_rgb(img)
        assert result.mode == "RGB"
        assert result.size == (50, 50)

    def test_la_to_rgb(self):
        img = Image.new("LA", (30, 30), (128, 255))
        result = to_rgb(img)
        assert result.mode == "RGB"

    def test_p_mode_to_rgb(self):
        rgb_img = Image.new("RGB", (20, 20), (100, 200, 50))
        p_img = rgb_img.convert("P")
        result = to_rgb(p_img)
        assert result.mode == "RGB"


class TestScaleImage:
    def _make_img(self, w: int, h: int) -> Image.Image:
        return Image.new("RGB", (w, h), (200, 200, 200))

    def test_stretch_mode(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 150, ScaleMode.STRETCH)
        scale = 150 / 72.0
        target_w = int(600 * scale)
        target_h = int(800 * scale)
        assert result.size == (target_w, target_h)

    def test_fit_width_mode(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 150, ScaleMode.FIT_WIDTH)
        scale = 150 / 72.0
        target_w = int(600 * scale)
        assert result.size[0] == target_w

    def test_fit_height_mode(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 150, ScaleMode.FIT_HEIGHT)
        scale = 150 / 72.0
        target_h = int(800 * scale)
        assert result.size[1] == target_h

    def test_fill_crop_mode(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 150, ScaleMode.FILL_CROP)
        assert result.mode == "RGB"

    def test_fit_mode(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 150, ScaleMode.FIT)
        scale = 150 / 72.0
        target_w = int(600 * scale)
        target_h = int(800 * scale)
        assert result.size[0] <= target_w
        assert result.size[1] <= target_h

    def test_dpi_zero_keeps_original_size(self):
        img = self._make_img(400, 300)
        result = scale_image(img, 600, 800, 0, ScaleMode.STRETCH)
        assert result.size == (400, 300)

    def test_zero_size_image_returns_unchanged(self):
        img = self._make_img(0, 0)
        result = scale_image(img, 600, 800, 150, ScaleMode.FILL_CROP)
        assert result.size == (0, 0)

    def test_p_mode_image_handled(self):
        rgb_img = Image.new("RGB", (100, 100), (100, 150, 200))
        p_img = rgb_img.convert("P")
        result = scale_image(p_img, 500, 500, 150, ScaleMode.FIT)
        result = to_rgb(result)
        assert result.mode == "RGB"

    def test_fit_mode_creates_canvas_smaller(self):
        img = self._make_img(200, 100)
        result = scale_image(img, 600, 800, 72, ScaleMode.FIT)
        assert result.size[0] <= 600
        assert result.size[1] <= 800
