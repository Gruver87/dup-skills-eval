"""Security scan — secrets, download-exec, dangerous enable patterns."""

from __future__ import annotations

import re
from pathlib import Path

from skills_eval.models import Finding, Severity

# Heuristic secret / credential patterns (fail-closed on match in skill text).
_SECRET_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "aws_access_key",
        re.compile(r"AKIA[0-9A-Z]{16}"),
    ),
    (
        "private_key_block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "generic_api_key_assign",
        re.compile(
            r"(?i)(?:api[_-]?key|secret[_-]?key|access[_-]?token|private[_-]?key)"
            r"\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"
        ),
    ),
    (
        "sk_live_token",
        re.compile(r"sk-(?:live|test|proj)-[A-Za-z0-9]{16,}"),
    ),
    (
        "jwt_like",
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
]

_DOWNLOAD_EXEC = re.compile(
    r"(?i)(curl|wget)\s+[^\n|]*\|\s*(?:ba)?sh"
    r"|(?:iwr|Invoke-WebRequest).*\|\s*iex"
    r"|Invoke-Expression\s*\(\s*\(Invoke-WebRequest",
)

_TEXT_GLOBS = ("*.md", "*.ps1", "*.py", "*.sh", "*.js", "*.ts", "*.json", "*.toml")


def _iter_text_files(skill_dir: Path) -> list[Path]:
    files: list[Path] = []
    for pattern in _TEXT_GLOBS:
        files.extend(skill_dir.rglob(pattern))
    # Dedup, skip caches
    out: list[Path] = []
    seen: set[Path] = set()
    for p in files:
        if p in seen:
            continue
        if any(part in {".git", "__pycache__", ".ruff_cache", "node_modules"} for part in p.parts):
            continue
        seen.add(p)
        out.append(p)
    return out


def scan_skill_dir(skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    folder = skill_dir.name
    for path in _iter_text_files(skill_dir):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(
                Finding(
                    gate="security",
                    skill=folder,
                    code="unreadable_file",
                    message=f"cannot read as utf-8: {path.name}",
                    path=str(path),
                    severity=Severity.WARN,
                )
            )
            continue
        for code, pat in _SECRET_PATTERNS:
            if pat.search(text):
                findings.append(
                    Finding(
                        gate="security",
                        skill=folder,
                        code=code,
                        message=f"possible secret material in {path.name}",
                        path=str(path),
                    )
                )
        if _DOWNLOAD_EXEC.search(text):
            findings.append(
                Finding(
                    gate="security",
                    skill=folder,
                    code="download_exec",
                    message=f"download-and-execute pattern in {path.name}",
                    path=str(path),
                )
            )
    return findings


def scan_pack_root_extras(pack_root: Path) -> list[Finding]:
    """Scan pack-level scripts that accompany skills (optional)."""
    findings: list[Finding] = []
    scripts = pack_root / "scripts"
    if not scripts.is_dir():
        return findings
    for path in list(scripts.glob("*.ps1")) + list(scripts.glob("*.py")):
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        if _DOWNLOAD_EXEC.search(text):
            findings.append(
                Finding(
                    gate="security",
                    skill="*",
                    code="download_exec",
                    message=f"download-and-execute pattern in scripts/{path.name}",
                    path=str(path),
                )
            )
        for code, pat in _SECRET_PATTERNS:
            if pat.search(text):
                findings.append(
                    Finding(
                        gate="security",
                        skill="*",
                        code=code,
                        message=f"possible secret material in scripts/{path.name}",
                        path=str(path),
                    )
                )
    return findings
