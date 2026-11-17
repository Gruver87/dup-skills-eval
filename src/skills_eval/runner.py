"""Orchestrate static + security + honesty gates over a skills pack."""

from __future__ import annotations

from pathlib import Path

from skills_eval import __version__
from skills_eval.honesty_gate import check_pack_policy, check_skill_honesty
from skills_eval.models import EvalReport, Finding
from skills_eval.security_scan import scan_pack_root_extras, scan_skill_dir
from skills_eval.static_gate import (
    check_mirrors,
    check_version_pin,
    list_skill_dirs,
    validate_skill_dir,
)


def resolve_skills_root(pack_root: Path, skills_subdir: str = "skills") -> Path:
    pack_root = pack_root.resolve()
    candidate = pack_root / skills_subdir
    if candidate.is_dir():
        return candidate
    # Allow pointing directly at a skills/ directory.
    if pack_root.name == "skills" and pack_root.is_dir():
        return pack_root
    return candidate


def evaluate_pack(
    pack_root: Path,
    *,
    skills_subdir: str = "skills",
    skip_security: bool = False,
    skip_honesty: bool = False,
) -> EvalReport:
    pack_root = pack_root.resolve()
    skills_root = resolve_skills_root(pack_root, skills_subdir)
    findings: list[Finding] = []
    versions: dict[str, str] = {}

    if not skills_root.is_dir():
        findings.append(
            Finding(
                gate="static",
                skill="*",
                code="skills_missing",
                message=f"skills directory missing: {skills_root}",
                path=str(skills_root),
            )
        )
        return EvalReport(
            pack_root=str(pack_root),
            skills_root=str(skills_root),
            skill_count=0,
            findings=findings,
            tool_version=__version__,
        )

    skill_dirs = list_skill_dirs(skills_root)
    if not skill_dirs:
        findings.append(
            Finding(
                gate="static",
                skill="*",
                code="no_skills",
                message="no skill directories under skills/",
                path=str(skills_root),
            )
        )

    for d in skill_dirs:
        skill_findings, ver = validate_skill_dir(d)
        findings.extend(skill_findings)
        if ver:
            versions[d.name] = ver
        if not skip_security:
            findings.extend(scan_skill_dir(d))
        if not skip_honesty:
            findings.extend(check_skill_honesty(d))

    findings.extend(check_mirrors(pack_root, skill_dirs))
    pin_findings, pin = check_version_pin(pack_root, versions)
    findings.extend(pin_findings)

    if not skip_security:
        findings.extend(scan_pack_root_extras(pack_root))
    if not skip_honesty:
        findings.extend(check_pack_policy(pack_root, skill_dirs))

    return EvalReport(
        pack_root=str(pack_root),
        skills_root=str(skills_root),
        skill_count=len(skill_dirs),
        findings=findings,
        versions=versions,
        pin=pin,
        tool_version=__version__,
    )
