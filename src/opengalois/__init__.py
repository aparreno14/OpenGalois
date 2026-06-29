from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("opengalois")
except PackageNotFoundError:
    __version__ = "0.0.0"

from .api import analyze, render_explanation, verify  # noqa: E402
from .models import AnalysisOptions, GaloisGroup, Result, Status, VerifiedResult  # noqa: E402

__all__ = [
    "__version__",
    "analyze",
    "verify",
    "render_explanation",
    "AnalysisOptions",
    "Result",
    "VerifiedResult",
    "Status",
    "GaloisGroup",
]
