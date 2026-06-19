from __future__ import annotations

import pytest
from rcsw.core.detector import (
    _filter_by_size,
    _match_position,
)
from rcsw.core.models import (
    ScaleMode,
    WatermarkMode,
)

import fitz


class TestFilterBySize:
    def test_filters_images_below_max_size(self):
        imgs = [
            (10, "img", 100, 100),
            (20, "img", 800, 600),
            (30, "img", 200, 300),
        ]
        result = _filter_by_size(imgs, 500)
        assert result == [0, 2]

    def test_excludes_images_above_max_size(self):
        imgs = [(10, "img", 600, 500)]
        result = _filter_by_size(imgs, 500)
        assert result == []

    def test_edge_case_equal_to_max_size(self):
        imgs = [(10, "img", 500, 500)]
        result = _filter_by_size(imgs, 500)
        assert result == [0]

    def test_empty_list(self):
        result = _filter_by_size([], 500)
        assert result == []

    def test_zero_size_max(self):
        imgs = [(10, "img", 10, 10)]
        result = _filter_by_size(imgs, 0)
        assert result == []


class TestMatchPosition:
    def test_bottom_right_match(self):
        rect = fitz.Rect(860, 760, 900, 800)
        assert _match_position(rect, 1000, 850, WatermarkMode.BOTTOM_RIGHT)

    def test_bottom_right_no_match(self):
        rect = fitz.Rect(100, 100, 200, 200)
        assert not _match_position(rect, 1000, 850, WatermarkMode.BOTTOM_RIGHT)

    def test_bottom_left_match(self):
        rect = fitz.Rect(10, 760, 80, 800)
        assert _match_position(rect, 1000, 850, WatermarkMode.BOTTOM_LEFT)

    def test_top_right_match(self):
        rect = fitz.Rect(860, 10, 900, 50)
        assert _match_position(rect, 1000, 850, WatermarkMode.TOP_RIGHT)

    def test_top_left_match(self):
        rect = fitz.Rect(10, 10, 80, 50)
        assert _match_position(rect, 1000, 850, WatermarkMode.TOP_LEFT)

    def test_bottom_center_match(self):
        rect = fitz.Rect(450, 760, 550, 800)
        assert _match_position(rect, 1000, 850, WatermarkMode.BOTTOM_CENTER)

    def test_bottom_center_far_from_center(self):
        rect = fitz.Rect(100, 760, 200, 800)
        assert not _match_position(rect, 1000, 850, WatermarkMode.BOTTOM_CENTER)

    def test_auto_mode_returns_false(self):
        rect = fitz.Rect(0, 0, 100, 100)
        assert not _match_position(rect, 1000, 850, WatermarkMode.AUTO)


class TestScaleModeEnum:
    def test_all_modes_present(self):
        modes = list(ScaleMode)
        assert len(modes) == 5
        assert ScaleMode.FILL_CROP in modes
        assert ScaleMode.FIT in modes
        assert ScaleMode.STRETCH in modes
        assert ScaleMode.FIT_WIDTH in modes
        assert ScaleMode.FIT_HEIGHT in modes

    def test_scale_mode_labels_cover_all(self):
        from rcsw.core.models import SCALE_MODE_LABELS
        for mode in ScaleMode:
            assert mode in SCALE_MODE_LABELS


class TestWatermarkModeEnum:
    def test_all_modes_present(self):
        modes = list(WatermarkMode)
        assert len(modes) == 6

    def test_wm_mode_labels_cover_all(self):
        from rcsw.core.models import WM_MODE_LABELS
        for mode in WatermarkMode:
            assert mode in WM_MODE_LABELS


class TestTierFromDpiQ:
    def test_dpi_zero_maps_to_original(self):
        from rcsw.core.models import tier_from_dpi_q
        assert tier_from_dpi_q(0, 100) == 3

    def test_high_quality_params(self):
        from rcsw.core.models import tier_from_dpi_q
        assert tier_from_dpi_q(300, 95) == 2

    def test_medium_quality_params(self):
        from rcsw.core.models import tier_from_dpi_q
        assert tier_from_dpi_q(200, 90) == 1

    def test_low_quality_params(self):
        from rcsw.core.models import tier_from_dpi_q
        assert tier_from_dpi_q(150, 75) == 0

    def test_custom_params_find_closest(self):
        from rcsw.core.models import tier_from_dpi_q
        assert tier_from_dpi_q(220, 92) == 1
