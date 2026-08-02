"""
GUI Package for Monitor Layout Manager
Contains advanced GUI components and widgets.

The re-export is lazy (PEP 562) so importing the package — e.g. for
gui.canvas_math in headless test environments — never pulls in tkinter.
"""

__all__ = ['AdvancedMonitorLayoutManager']


def __getattr__(name):
    if name == 'AdvancedMonitorLayoutManager':
        from .advanced_layout_manager import AdvancedMonitorLayoutManager
        return AdvancedMonitorLayoutManager
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
