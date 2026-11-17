from __future__ import annotations

from pathlib import Path

from skills_eval.honesty_gate import check_pack_policy, check_skill_honesty
from skills_eval.static_gate import list_skill_dirs

FIXTURES = Path(__file__).parent / "fixtures"


def test_good_skill_honesty_clean() -> None:
    findings = check_skill_honesty(FIXTURES / "good_pack" / "skills" / "sample-skill")
    assert findings == []


def test_bad_skill_futures_and_soak() -> None:
    findings = check_skill_honesty(FIXTURES / "bad_pack" / "skills" / "Broken_Name")
    codes = {f.code for f in findings}
    assert "futures_enable_without_refuse" in codes
    assert "soak_pass_claim" in codes


def test_trading_pack_without_policy_fails() -> None:
    root = FIXTURES / "bad_pack"
    dirs = list_skill_dirs(root / "skills")
    findings = check_pack_policy(root, dirs)
    codes = {f.code for f in findings}
    assert "no_futures_policy_missing" in codes
