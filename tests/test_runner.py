from __future__ import annotations

from pathlib import Path

from skills_eval.runner import evaluate_pack

FIXTURES = Path(__file__).parent / "fixtures"


def test_good_pack_ok() -> None:
    report = evaluate_pack(FIXTURES / "good_pack")
    assert report.ok
    assert report.skill_count == 1
    assert report.pin == "0.1.0"


def test_bad_pack_fails() -> None:
    report = evaluate_pack(FIXTURES / "bad_pack")
    assert not report.ok
    assert len(report.errors) >= 3
    codes = {f.code for f in report.findings}
    assert "version_pin_mismatch" in codes or "invalid_dir_name" in codes
