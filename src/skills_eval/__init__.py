"""DUP Skills Eval — fail-closed industrial gate for Agent Skills packs."""

from __future__ import annotations

__version__ = "0.1.1"

from skills_eval.models import EvalReport, Finding, Severity
from skills_eval.runner import evaluate_pack

__all__ = [
    "__version__",
    "EvalReport",
    "Finding",
    "Severity",
    "evaluate_pack",
]
