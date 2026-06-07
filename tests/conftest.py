"""Pytest fixtures: a synthetic chart + bbox so pipeline tests don't depend on real data."""

from __future__ import annotations

import numpy as np
import pytest


@pytest.fixture
def synthetic_chart() -> np.ndarray:
    """800x800 white grayscale ([0,1] float) with a thick black '|' downstroke
    from (400, 200) to (400, 600). Useful as a stand-in for a Loth-style glyph.
    """
    img = np.ones((800, 800), dtype=np.float32)
    img[200:600, 392:408] = 0.05  # 16px wide vertical bar
    return img


@pytest.fixture
def synthetic_bbox() -> dict:
    """Bbox that fully contains the synthetic glyph and sets baseline/midband
    so the x-height pixel unit is 100 (== a 1.0 unit in template coords).
    """
    return {
        "y0": 100,
        "y1": 700,
        "x0": 300,
        "x1": 500,
        "mask_strokes": [],
        "baseline_y": 600,
        "midband_y": 500,
        "n_anchors": 30,
    }


@pytest.fixture
def synthetic_chart_path(tmp_path, synthetic_chart) -> str:
    """Persist the synthetic chart to disk and return its absolute path."""
    from PIL import Image

    out = tmp_path / "chart.png"
    Image.fromarray((synthetic_chart * 255).astype(np.uint8), mode="L").save(out)
    return str(out)
