"""rupdf - A fast, minimal PDF page renderer."""

from importlib.metadata import PackageNotFoundError, version as _pkg_version

from rupdf._rupdf import render_pdf, RupdfError

__all__ = ["render_pdf", "RupdfError"]

try:
    __version__ = _pkg_version("rupdf")
except PackageNotFoundError:
    # Editable or source install with no installed metadata; not worth failing.
    __version__ = "unknown"
