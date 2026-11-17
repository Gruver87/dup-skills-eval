"""Static layout gate — agentskills.io naming + DUP pin rules."""

from __future__ import annotations

import json
import re
from pathlib import Path

from skills_eval.frontmatter import parse_frontmatter, strip_frontmatter
from skills_eval.models import Finding, Severity

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"(?m)^  version:\s*[\"']?([^\"'\s]+)[\"']?\s*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def _json_version(path: Path) -> str | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    ver = data.get("version")
    return str(ver).strip() if ver is not None else None


def list_skill_dirs(skills_root: Path) -> list[Path]:
    if not skills_root.is_dir():
        return []
    return sorted(
        p for p in skills_root.iterdir() if p.is_dir() and not p.name.startswith(".")
    )


def validate_skill_dir(dir_path: Path) -> tuple[list[Finding], str | None]:
    """Return findings and optional metadata.version for one skill directory."""
    findings: list[Finding] = []
    folder = dir_path.name
    skill_md = dir_path / "SKILL.md"
    if not skill_md.is_file():
        return (
            [
                Finding(
                    gate="static",
                    skill=folder,
                    code="missing_skill_md",
                    message="missing SKILL.md",
                    path=str(dir_path),
                )
            ],
            None,
        )

    if (
        not NAME_RE.match(folder)
        or "--" in folder
        or folder.startswith("-")
        or folder.endswith("-")
    ):
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="invalid_dir_name",
                message="invalid directory name (agentskills charset)",
                path=str(dir_path),
            )
        )
    if len(folder) > 64:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="name_too_long",
                message="name longer than 64 characters",
                path=str(dir_path),
            )
        )

    text = skill_md.read_text(encoding="utf-8")
    try:
        meta = parse_frontmatter(text)
    except ValueError as exc:
        return (
            [
                Finding(
                    gate="static",
                    skill=folder,
                    code="frontmatter",
                    message=str(exc),
                    path=str(skill_md),
                )
            ],
            None,
        )

    name = (meta.get("name") or "").strip()
    desc = (meta.get("description") or "").strip()
    if not name:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="missing_name",
                message="missing name in frontmatter",
                path=str(skill_md),
            )
        )
    elif name != folder:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="name_mismatch",
                message=f"name={name!r} must match folder",
                path=str(skill_md),
            )
        )
    elif not NAME_RE.match(name):
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="name_charset",
                message="name fails agentskills charset rules",
                path=str(skill_md),
            )
        )

    if not desc:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="missing_description",
                message="missing description",
                path=str(skill_md),
            )
        )
    elif len(desc) > 1024:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="description_too_long",
                message=f"description > 1024 chars ({len(desc)})",
                path=str(skill_md),
            )
        )

    if not (meta.get("license") or "").strip():
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="missing_license",
                message="missing license field",
                path=str(skill_md),
            )
        )

    version: str | None = None
    vm = VERSION_RE.search(text)
    if not vm:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="missing_version",
                message="missing metadata.version",
                path=str(skill_md),
            )
        )
    else:
        version = vm.group(1).strip()
        if not SEMVER_RE.match(version):
            findings.append(
                Finding(
                    gate="static",
                    skill=folder,
                    code="bad_semver",
                    message=f"metadata.version not semver ({version!r})",
                    path=str(skill_md),
                )
            )

    body = strip_frontmatter(text)
    if len(body.splitlines()) > 500:
        findings.append(
            Finding(
                gate="static",
                skill=folder,
                code="body_too_long",
                message="SKILL.md body > 500 lines (progressive disclosure)",
                path=str(skill_md),
                severity=Severity.WARN,
            )
        )

    return findings, version


def check_mirrors(pack_root: Path, skill_dirs: list[Path]) -> list[Finding]:
    agents = pack_root / ".agents" / "skills"
    if not agents.is_dir():
        return []
    findings: list[Finding] = []
    for d in skill_dirs:
        mirror = agents / d.name / "SKILL.md"
        if not mirror.is_file():
            findings.append(
                Finding(
                    gate="static",
                    skill=d.name,
                    code="mirror_missing",
                    message=f"mirror missing: .agents/skills/{d.name}/SKILL.md",
                    path=str(mirror),
                )
            )
    return findings


def check_version_pin(
    pack_root: Path, versions: dict[str, str]
) -> tuple[list[Finding], str | None]:
    findings: list[Finding] = []
    pin = _json_version(pack_root / "plugin.json")
    if not pin:
        # Packs without plugin.json are allowed; pin check skipped with info.
        if (pack_root / "plugin.json").exists() is False:
            return findings, None
        findings.append(
            Finding(
                gate="static",
                skill="*",
                code="plugin_missing_version",
                message="plugin.json: missing version",
                path=str(pack_root / "plugin.json"),
            )
        )
        return findings, None

    for folder, ver in sorted(versions.items()):
        if ver != pin:
            findings.append(
                Finding(
                    gate="static",
                    skill=folder,
                    code="version_pin_mismatch",
                    message=f"metadata.version={ver!r} != plugin.json {pin!r}",
                )
            )

    cursor_pin = _json_version(pack_root / ".cursor-plugin" / "plugin.json")
    if (pack_root / ".cursor-plugin" / "plugin.json").is_file():
        if not cursor_pin:
            findings.append(
                Finding(
                    gate="static",
                    skill="*",
                    code="cursor_plugin_missing_version",
                    message=".cursor-plugin/plugin.json: missing version",
                )
            )
        elif cursor_pin != pin:
            findings.append(
                Finding(
                    gate="static",
                    skill="*",
                    code="cursor_plugin_pin_mismatch",
                    message=(
                        f".cursor-plugin/plugin.json version={cursor_pin!r} "
                        f"!= plugin.json {pin!r}"
                    ),
                )
            )

    pkg = pack_root / "packages" / "radar_mcp" / "pyproject.toml"
    if pkg.is_file():
        m = re.search(
            r'(?m)^version\s*=\s*"([^"]+)"', pkg.read_text(encoding="utf-8")
        )
        if not m:
            findings.append(
                Finding(
                    gate="static",
                    skill="*",
                    code="radar_mcp_missing_version",
                    message="packages/radar_mcp/pyproject.toml: missing version",
                    path=str(pkg),
                )
            )
        elif m.group(1) != pin:
            findings.append(
                Finding(
                    gate="static",
                    skill="*",
                    code="radar_mcp_pin_mismatch",
                    message=(
                        f"radar_mcp pyproject version={m.group(1)!r} "
                        f"!= plugin.json {pin!r}"
                    ),
                    path=str(pkg),
                )
            )

    return findings, pin
