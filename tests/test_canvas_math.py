"""
Unit tests for gui.canvas_math — the pure geometry behind the layout canvas.

The coordinate convention under test matches displayplacer/CoreGraphics:
(0,0) = main display's top-left, y grows DOWN.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui.canvas_math import (  # noqa: E402
    Rect,
    arrangement_bounds,
    canvas_to_display,
    clamp_to_view,
    display_to_canvas,
    fit_offset,
    is_contiguous,
    overlaps,
    snap_position,
)

# A realistic 3-display arrangement (mirrors a MacBook with one monitor above
# it and one up-left, i.e. NEGATIVE origins — the case the old code mirrored).
MACBOOK = Rect(0, 0, 1728, 1117)
ABOVE = Rect(1728, -996, 1920, 1080)
UP_LEFT = Rect(-192, -1080, 1920, 1080)


class TestTransformRoundTrip:
    def test_identity_at_origin(self):
        offset = (0.0, 0.0)
        assert display_to_canvas(0, 0, offset, 0.1) == (0.0, 0.0)
        assert canvas_to_display(0, 0, offset, 0.1) == (0, 0)

    def test_round_trip(self):
        offset = (123.4, 567.8)
        scale = 0.1
        for x, y in [(0, 0), (1728, -996), (-192, -1080), (5000, 3000)]:
            cx, cy = display_to_canvas(x, y, offset, scale)
            assert canvas_to_display(cx, cy, offset, scale) == (x, y)

    def test_y_axis_is_not_flipped(self):
        """A display ABOVE the main (negative y) must render ABOVE it on canvas."""
        offset = (400.0, 400.0)
        _, main_cy = display_to_canvas(MACBOOK.x, MACBOOK.y, offset, 0.1)
        _, above_cy = display_to_canvas(ABOVE.x, ABOVE.y, offset, 0.1)
        assert above_cy < main_cy

    def test_negative_coordinates_supported(self):
        offset = (500.0, 500.0)
        cx, cy = display_to_canvas(-192, -1080, offset, 0.1)
        assert cx < 500 and cy < 500


class TestBoundsAndFit:
    def test_bounds_single(self):
        assert arrangement_bounds([MACBOOK]) == Rect(0, 0, 1728, 1117)

    def test_bounds_with_negative_origins(self):
        b = arrangement_bounds([MACBOOK, ABOVE, UP_LEFT])
        assert b.x == -192
        assert b.y == -1080
        assert b.right == 1728 + 1920
        assert b.bottom == 1117

    def test_bounds_empty(self):
        assert arrangement_bounds([]) == Rect(0, 0, 0, 0)

    def test_fit_centers_arrangement(self):
        rects = [MACBOOK, ABOVE, UP_LEFT]
        canvas_w, canvas_h, scale = 800, 600, 0.1
        offset = fit_offset(rects, canvas_w, canvas_h, scale)
        b = arrangement_bounds(rects)
        cx, cy = display_to_canvas(b.x + b.w / 2, b.y + b.h / 2, offset, scale)
        assert abs(cx - canvas_w / 2) < 1e-6
        assert abs(cy - canvas_h / 2) < 1e-6

    def test_fit_keeps_arrangement_fully_visible_at_sane_zoom(self):
        rects = [MACBOOK, ABOVE, UP_LEFT]
        offset = fit_offset(rects, 800, 600, 0.1)
        for r in rects:
            x1, y1 = display_to_canvas(r.x, r.y, offset, 0.1)
            x2, y2 = display_to_canvas(r.right, r.bottom, offset, 0.1)
            assert 0 <= x1 <= 800 and 0 <= x2 <= 800
            assert 0 <= y1 <= 600 and 0 <= y2 <= 600


class TestSnapping:
    def test_snaps_left_edge_to_neighbors_right_edge(self):
        moving = Rect(1740, 100, 1920, 1080)   # 12px short of flush at x=1728
        x, y = snap_position(moving, [MACBOOK], threshold=50)
        assert x == 1728
        assert y == 100

    def test_snaps_right_edge_to_neighbors_left_edge(self):
        moving = Rect(-1935, 100, 1920, 1080)  # 15px off flush at x=-1920
        x, _ = snap_position(moving, [MACBOOK], threshold=50)
        assert x == -1920

    def test_snaps_top_edge_below_neighbor(self):
        moving = Rect(100, 1130, 1920, 1080)   # 13px below flush at y=1117
        _, y = snap_position(moving, [MACBOOK], threshold=50)
        assert y == 1117

    def test_snaps_bottom_edge_above_neighbor(self):
        moving = Rect(100, -1090, 1920, 1080)  # bottom at -10, flush would be 0 → y=-1080
        _, y = snap_position(moving, [MACBOOK], threshold=50)
        assert y == -1080

    def test_no_snap_outside_threshold(self):
        moving = Rect(1900, 100, 1920, 1080)   # 172px away from flush
        x, y = snap_position(moving, [MACBOOK], threshold=50)
        assert (x, y) == (1900, 100)

    def test_no_horizontal_snap_without_vertical_overlap(self):
        # Same near-flush x, but the moving rect is far below — projections
        # don't overlap so the adjacency snap must not fire.
        moving = Rect(1740, 5000, 1920, 1080)
        x, _ = snap_position(moving, [MACBOOK], threshold=50)
        assert x == 1740

    def test_aligns_tops_when_side_by_side(self):
        # Flush on x, tops 9px apart → top-top alignment should fire.
        moving = Rect(1728, 9, 1920, 1080)
        x, y = snap_position(moving, [MACBOOK], threshold=20)
        assert x == 1728
        assert y == 0

    def test_aligns_bottoms_when_side_by_side(self):
        # Flush on x, bottom 8px above the MacBook's bottom (1117).
        moving = Rect(1728, 1117 - 1080 + 8, 1920, 1080)
        x, y = snap_position(moving, [MACBOOK], threshold=20)
        assert x == 1728
        assert y == 1117 - 1080

    def test_nearest_candidate_wins(self):
        left = Rect(0, 0, 1000, 1000)
        right = Rect(3000, 0, 1000, 1000)
        # 5px from flush against `left`, 25px from flush against `right`
        moving = Rect(1005, 100, 1970, 1000)
        x, _ = snap_position(moving, [left, right], threshold=50)
        assert x == 1000

    def test_snap_result_is_int(self):
        moving = Rect(1740, 100, 1920, 1080)
        x, y = snap_position(moving, [MACBOOK], threshold=50)
        assert isinstance(x, int) and isinstance(y, int)


class TestClampToView:
    def test_inside_stays_put(self):
        assert clamp_to_view(100, 100, 200, 150, 800, 600, margin=24) == (100, 100)

    def test_cannot_escape_right(self):
        x, _ = clamp_to_view(5000, 100, 200, 150, 800, 600, margin=24)
        assert x == 800 - 24

    def test_cannot_escape_left(self):
        x, _ = clamp_to_view(-5000, 100, 200, 150, 800, 600, margin=24)
        assert x == 24 - 200

    def test_cannot_escape_bottom(self):
        _, y = clamp_to_view(100, 5000, 200, 150, 800, 600, margin=24)
        assert y == 600 - 24

    def test_cannot_escape_top(self):
        _, y = clamp_to_view(100, -5000, 200, 150, 800, 600, margin=24)
        assert y == 24 - 150


class TestContiguityAndOverlap:
    def test_single_display_contiguous(self):
        assert is_contiguous([MACBOOK])

    def test_flush_row_contiguous(self):
        right = Rect(1728, 0, 1920, 1080)
        assert is_contiguous([MACBOOK, right])

    def test_gap_not_contiguous(self):
        gapped = Rect(1828, 0, 1920, 1080)
        assert not is_contiguous([MACBOOK, gapped])

    def test_corner_touch_not_contiguous(self):
        # Sharing only a corner point is not an edge — macOS shifts these.
        corner = Rect(1728, 1117, 1920, 1080)
        assert not is_contiguous([MACBOOK, corner])

    def test_chain_of_three_contiguous(self):
        mid = Rect(1728, 0, 1920, 1080)
        far = Rect(1728 + 1920, 0, 1920, 1080)
        assert is_contiguous([MACBOOK, mid, far])

    def test_stacked_contiguous(self):
        above = Rect(0, -1080, 1920, 1080)
        assert is_contiguous([MACBOOK, above])

    def test_no_overlap_when_flush(self):
        right = Rect(1728, 0, 1920, 1080)
        assert not overlaps([MACBOOK, right])

    def test_overlap_detected(self):
        overlapping = Rect(1000, 500, 1920, 1080)
        assert overlaps([MACBOOK, overlapping])
