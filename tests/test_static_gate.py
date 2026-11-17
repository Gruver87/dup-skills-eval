from __future__ import annotations

from pathlib import Path

from skills_eval.static_gate import list_skill_dirs, validate_skill_dir

FIXTURES = Path(__file__).parent / "fixtures"


def test_good_skill_passes() -> None:
    d = FIXTURES / "good_pack" / "skills" / "sample-skill"
    findings, ver = validate_skill_dir(d)
    errors = [f for f in findings if f.severity.value == "error"]
    assert errors == []
    assert ver == "0.1.0"


def test_bad_skill_collects_static_errors() -> None:
    d = FIXTURES / "bad_pack" / "skills" / "Broken_Name"
    findings, _ver = validate_skill_dir(d)
    codes = {f.code for f in findings}
    assert "invalid_dir_name" in codes
    assert "name_mismatch" in codes
    assert "missing_license" in codes
    assert "missing_version" in codes


def test_list_skill_dirs() -> None:
    dirs = list_skill_dirs(FIXTURES / "good_pack" / "skills")
    assert [d.name for d in dirs] == ["sample-skill"]
