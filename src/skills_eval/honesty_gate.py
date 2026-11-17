"""Honesty / policy gate for DUP market-ops skill packs."""

from __future__ import annotations

import re
from pathlib import Path

from skills_eval.models import Finding, Severity

# Obsolete GitHub names must not appear as current repo URLs in skill text.
_OBSOLETE_REPO = re.compile(
    r"(?i)github\.com/Gruver87/(?:experimental|Absolute_Blockchain_Ultimate_Hybrid)\b"
)

# Soft claim language that needs pack context — warn if soak PASS without refuse.
_SOAK_PASS_CLAIM = re.compile(
    r"(?i)\b(?:48\s*h|48h)\s+soak\b.*\b(?:pass|passed|green)\b"
    r"|\bsoak\s+(?:pass|passed)\b"
)

# Enabling futures auto without hard refuse nearby.
_FUTURES_ENABLE = re.compile(
    r"(?i)\b(?:enable|turn\s+on|unlock)\b.{0,40}\bfutures?\s+auto\b"
    r"|\bfutures?\s+auto\b.{0,40}\b(?:enable|true|on)\b"
)

_REFUSE_NEAR = re.compile(
    r"(?i)\b(?:refuse|forbidden|never|block|out\s+of\s+scope|FUTURES_BLOCK)\b"
)

# Packs that look like trading/market ops should carry no-futures policy somewhere.
_TRADING_HINT = re.compile(
    r"(?i)\b(?:kucoin|spot\s+entr|live\s+money|radar|futures|order|trade)\b"
)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def check_skill_honesty(skill_dir: Path) -> list[Finding]:
    findings: list[Finding] = []
    folder = skill_dir.name
    skill_md = skill_dir / "SKILL.md"
    text = _read(skill_md)
    if not text:
        return findings

    if _OBSOLETE_REPO.search(text):
        findings.append(
            Finding(
                gate="honesty",
                skill=folder,
                code="obsolete_github_url",
                message=(
                    "obsolete Gruver87 repo URL — use dup-protocol / "
                    "dup-protocol-experimental"
                ),
                path=str(skill_md),
            )
        )

    for m in _SOAK_PASS_CLAIM.finditer(text):
        window = text[max(0, m.start() - 200) : m.end() + 200]
        # Pedagogical refuse / inequality / checklist framing — not a real claim.
        if re.search(
            r"(?i)(?:\b(?:do\s+not|never|only\s+if|unless|not\s+claim|must\s+not|"
            r"refuse|forbidden|equat(?:e|ing)|invented|without|asks?|"
            r"approx_48h_claim_ok)\b"
            r"|≠|!="
            r"|\bops-ready\b"
            r"|\bno\s+soak\b"
            r"|\bnot\s+claimed\b)",
            window,
        ):
            continue
        findings.append(
            Finding(
                gate="honesty",
                skill=folder,
                code="soak_pass_claim",
                message="possible soak PASS claim without refuse framing",
                path=str(skill_md),
                severity=Severity.WARN,
            )
        )
        break

    for m in _FUTURES_ENABLE.finditer(text):
        window = text[max(0, m.start() - 80) : m.end() + 80]
        if not _REFUSE_NEAR.search(window):
            findings.append(
                Finding(
                    gate="honesty",
                    skill=folder,
                    code="futures_enable_without_refuse",
                    message="futures auto enable language without refuse/block nearby",
                    path=str(skill_md),
                )
            )
            break

    return findings


def check_pack_policy(pack_root: Path, skill_dirs: list[Path]) -> list[Finding]:
    """If pack looks trading-related, require no-futures-auto skill or strong needle."""
    findings: list[Finding] = []
    names = {d.name for d in skill_dirs}
    corpus_parts: list[str] = []
    for d in skill_dirs:
        corpus_parts.append(_read(d / "SKILL.md"))
    readme = pack_root / "README.md"
    if readme.is_file():
        corpus_parts.append(_read(readme))
    corpus = "\n".join(corpus_parts)

    if not _TRADING_HINT.search(corpus):
        return findings

    if "no-futures-auto" in names:
        return findings

    # Fallback: strong FUTURES_BLOCK / refuse futures needle across pack
    if re.search(r"(?i)\bFUTURES_BLOCK\b|\bnever\b.{0,30}\bfutures?\s+auto\b", corpus):
        findings.append(
            Finding(
                gate="honesty",
                skill="*",
                code="no_futures_skill_missing",
                message=(
                    "trading-related pack without no-futures-auto skill "
                    "(needle present — warn only)"
                ),
                severity=Severity.WARN,
            )
        )
        return findings

    findings.append(
        Finding(
            gate="honesty",
            skill="*",
            code="no_futures_policy_missing",
            message=(
                "trading-related pack missing no-futures-auto skill "
                "and FUTURES_BLOCK / refuse needle"
            ),
        )
    )
    return findings
