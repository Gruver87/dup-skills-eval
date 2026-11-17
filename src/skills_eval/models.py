"""Shared result types for the evaluation gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any


class Severity(StrEnum):
    ERROR = "error"
    WARN = "warn"
    INFO = "info"


@dataclass(frozen=True)
class Finding:
    gate: str
    skill: str
    code: str
    message: str
    severity: Severity = Severity.ERROR
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class EvalReport:
    pack_root: str
    skills_root: str
    skill_count: int
    findings: list[Finding] = field(default_factory=list)
    versions: dict[str, str] = field(default_factory=dict)
    pin: str | None = None
    tool_version: str = "0.1.0"

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.severity is Severity.WARN]

    @property
    def ok(self) -> bool:
        return not self.errors

    def to_dict(self) -> dict[str, Any]:
        return {
            "tool_version": self.tool_version,
            "pack_root": self.pack_root,
            "skills_root": self.skills_root,
            "skill_count": self.skill_count,
            "pin": self.pin,
            "versions": dict(self.versions),
            "ok": self.ok,
            "error_count": len(self.errors),
            "warn_count": len(self.warnings),
            "findings": [f.to_dict() for f in self.findings],
        }
