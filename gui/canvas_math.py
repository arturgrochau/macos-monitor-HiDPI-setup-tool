"""
Pure geometry for the layout canvas — no tkinter imports, fully unit-testable.

Coordinate convention (matches displayplacer / CoreGraphics):
  (0,0) is the main display's TOP-LEFT corner, x grows right, y grows DOWN.
  A monitor physically above the main display has a negative y origin.

The canvas uses the same orientation, so display->canvas is a plain
scale + offset with no axis flip. The canvas is only ever a projection of
the display-space model; positions are never derived back from canvas items.
"""

from typing import Iterable, List, NamedTuple, Optional, Tuple


class Rect(NamedTuple):
    """Axis-aligned rectangle in display space (y-down)."""
    x: int
    y: int
    w: int
    h: int

    @property
    def right(self) -> int:
        return self.x + self.w

    @property
    def bottom(self) -> int:
        return self.y + self.h


def arrangement_bounds(rects: Iterable[Rect]) -> Rect:
    """Bounding box of all displays in display space."""
    rects = list(rects)
    if not rects:
        return Rect(0, 0, 0, 0)
    min_x = min(r.x for r in rects)
    min_y = min(r.y for r in rects)
    max_x = max(r.right for r in rects)
    max_y = max(r.bottom for r in rects)
    return Rect(min_x, min_y, max_x - min_x, max_y - min_y)


def fit_offset(rects: Iterable[Rect], canvas_w: int, canvas_h: int,
               scale: float) -> Tuple[float, float]:
    """Offset (in canvas px) that centers the arrangement in the canvas."""
    b = arrangement_bounds(rects)
    center_x = (b.x + b.w / 2) * scale
    center_y = (b.y + b.h / 2) * scale
    return canvas_w / 2 - center_x, canvas_h / 2 - center_y


def display_to_canvas(x: float, y: float, offset: Tuple[float, float],
                      scale: float) -> Tuple[float, float]:
    return x * scale + offset[0], y * scale + offset[1]


def canvas_to_display(cx: float, cy: float, offset: Tuple[float, float],
                      scale: float) -> Tuple[int, int]:
    return round((cx - offset[0]) / scale), round((cy - offset[1]) / scale)


def _overlap_len(a_start: float, a_len: float, b_start: float, b_len: float) -> float:
    """Length of the overlap of two 1-D segments."""
    return min(a_start + a_len, b_start + b_len) - max(a_start, b_start)


def snap_position(moving: Rect, others: Iterable[Rect],
                  threshold: float) -> Tuple[int, int]:
    """Return the snapped display-space position for `moving`.

    Snap candidates, per axis, against every stationary display:
      - adjacency: moving's edge flush against the other's opposite edge
        (only when the perpendicular projections overlap, so a display far
        above can't capture a horizontal snap)
      - alignment: matching edges (top-top / bottom-bottom, left-left /
        right-right), only when the displays are already adjacent or nearly
        adjacent on the perpendicular axis.

    The nearest candidate within `threshold` wins each axis independently.
    """
    best_dx: Optional[float] = None
    best_dy: Optional[float] = None

    def consider_x(delta: float):
        nonlocal best_dx
        if abs(delta) <= threshold and (best_dx is None or abs(delta) < abs(best_dx)):
            best_dx = delta

    def consider_y(delta: float):
        nonlocal best_dy
        if abs(delta) <= threshold and (best_dy is None or abs(delta) < abs(best_dy)):
            best_dy = delta

    for s in others:
        y_overlap = _overlap_len(moving.y, moving.h, s.y, s.h)
        x_overlap = _overlap_len(moving.x, moving.w, s.x, s.w)

        near_x_adjacent = (abs(s.x - moving.w - moving.x) <= threshold
                           or abs(s.right - moving.x) <= threshold)
        near_y_adjacent = (abs(s.y - moving.h - moving.y) <= threshold
                           or abs(s.bottom - moving.y) <= threshold)

        if y_overlap > 0:
            consider_x(s.x - moving.w - moving.x)   # my right edge to its left
            consider_x(s.right - moving.x)          # my left edge to its right
        if x_overlap > 0:
            consider_y(s.y - moving.h - moving.y)   # my bottom edge to its top
            consider_y(s.bottom - moving.y)         # my top edge to its bottom

        if near_x_adjacent:                          # beside it: align tops/bottoms
            consider_y(s.y - moving.y)
            consider_y(s.bottom - moving.h - moving.y)
        if near_y_adjacent:                          # above/below it: align lefts/rights
            consider_x(s.x - moving.x)
            consider_x(s.right - moving.w - moving.x)

    x = moving.x + (best_dx if best_dx is not None else 0)
    y = moving.y + (best_dy if best_dy is not None else 0)
    return round(x), round(y)


def clamp_to_view(x: float, y: float, w: float, h: float,
                  view_w: float, view_h: float, margin: float = 24) -> Tuple[float, float]:
    """Keep at least `margin` px of the rect inside the view (canvas space)."""
    x = max(margin - w, min(x, view_w - margin))
    y = max(margin - h, min(y, view_h - margin))
    return x, y


def _adjacent(a: Rect, b: Rect) -> bool:
    """True when a and b share an edge segment of positive length."""
    if a.right == b.x or b.right == a.x:
        return _overlap_len(a.y, a.h, b.y, b.h) > 0
    if a.bottom == b.y or b.bottom == a.y:
        return _overlap_len(a.x, a.w, b.x, b.w) > 0
    return False


def is_contiguous(rects: List[Rect]) -> bool:
    """True when every display is edge-connected to the arrangement.

    macOS silently shifts displays that don't share an edge with the rest,
    so a non-contiguous canvas will not apply as drawn.
    """
    if len(rects) <= 1:
        return True
    seen = {0}
    frontier = [0]
    while frontier:
        i = frontier.pop()
        for j in range(len(rects)):
            if j not in seen and _adjacent(rects[i], rects[j]):
                seen.add(j)
                frontier.append(j)
    return len(seen) == len(rects)


def overlaps(rects: List[Rect]) -> bool:
    """True when any two displays overlap by a positive area."""
    for i in range(len(rects)):
        for j in range(i + 1, len(rects)):
            a, b = rects[i], rects[j]
            if (_overlap_len(a.x, a.w, b.x, b.w) > 0
                    and _overlap_len(a.y, a.h, b.y, b.h) > 0):
                return True
    return False
