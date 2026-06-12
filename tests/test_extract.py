"""Per-glyph speck auto-fill (fill_small_holes) — fill small enclosed holes,
leave genuine counters and border-open notches alone."""

import numpy as np

from core.extract import binarize_adaptive, fill_small_holes


def _block_with_holes() -> np.ndarray:
    """A solid 40x40 ink block with a 3x3 speck (area 9) and an 11x11 counter
    (area 121) punched out of it."""
    mask = np.ones((40, 40), dtype=bool)
    mask[5:8, 5:8] = False  # speck, area 9
    mask[20:31, 20:31] = False  # counter, area 121
    return mask


def test_fill_small_holes_fills_speck_keeps_counter():
    mask = _block_with_holes()
    filled = fill_small_holes(mask, max_area=16)
    assert filled[5:8, 5:8].all()  # speck swallowed
    assert not filled[20:31, 20:31].any()  # counter still open
    assert int(filled.sum() - mask.sum()) == 9  # only the 9 speck pixels flipped


def test_fill_small_holes_noop_when_threshold_zero():
    mask = _block_with_holes()
    assert np.array_equal(fill_small_holes(mask, max_area=0), mask)


def test_fill_small_holes_ignores_background_open_to_edge():
    # A notch touching the image border is not an enclosed hole — stays background.
    mask = np.ones((20, 20), dtype=bool)
    mask[0:3, 9:11] = False
    out = fill_small_holes(mask, max_area=50)
    assert not out[0:3, 9:11].any()


def test_binarize_adaptive_fill_param_threads_through():
    # A dark block with a bright pinhole inside binarises to an enclosed hole;
    # the fill param closes it, fill=0 leaves it.
    gray = np.ones((60, 60), dtype=np.float32)
    gray[15:45, 15:45] = 0.0  # ink block
    gray[29:31, 29:31] = 1.0  # bright speck inside the ink
    raw = binarize_adaptive(gray, fill_holes_max_area=0)
    filled = binarize_adaptive(gray, fill_holes_max_area=16)
    assert not raw[29:31, 29:31].any()  # speck reads as background without fill
    assert filled[29:31, 29:31].all()  # …and as ink once filled
