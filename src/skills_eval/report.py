"""JSON + Markdown report writers."""

from __future__ import annotations

import json
from pathlib import Path

from skills_eval.models import EvalReport, Severity


def write_json(report: EvalReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report.to_dict(), indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def render_markdown(report: EvalReport) -> str:
    status = "PASS" if report.ok else "FAIL"
    lines = [
        f"# Skills Eval Report — {status}",
        "",
        f"- tool: `dup-skills-eval` `{report.tool_version}`",
        f"- pack: `{report.pack_root}`",
        f"- skills: `{report.skills_root}` (n={report.skill_count})",
        f"- pin: `{report.pin or 'n/a'}`",
        f"- errors: **{len(report.errors)}** · warnings: **{len(report.warnings)}**",
        "",
    ]
    if report.versions:
        lines.append("## Versions")
        lines.append("")
        for name, ver in sorted(report.versions.items()):
            lines.append(f"- `{name}` → `{ver}`")
        lines.append("")
    if not report.findings:
        lines.append("No findings.")
        lines.append("")
        return "\n".join(lines)

    lines.append("## Findings")
    lines.append("")
    lines.append("| Sev | Gate | Skill | Code | Message |")
    lines.append("|-----|------|-------|------|---------|")
    for f in report.findings:
        msg = f.message.replace("|", "\\|")
        lines.append(
            f"| {f.severity.value} | {f.gate} | `{f.skill}` | `{f.code}` | {msg} |"
        )
    lines.append("")
    if report.ok:
        lines.append("Gate exit: **0** (errors=0; warnings do not fail).")
    else:
        lines.append("Gate exit: **1** (fail-closed on errors).")
    lines.append("")
    return "\n".join(lines)


def write_markdown(report: EvalReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_markdown(report), encoding="utf-8")


def print_summary(report: EvalReport) -> None:
    status = "PASS" if report.ok else "FAIL"
    print(
        f"skills_eval {status} n={report.skill_count} "
        f"errors={len(report.errors)} warns={len(report.warnings)} "
        f"pin={report.pin or 'n/a'}"
    )
    for f in report.findings:
        if f.severity is Severity.INFO:
            continue
        print(f" - [{f.severity.value}] {f.gate}/{f.skill}: {f.code} — {f.message}")
