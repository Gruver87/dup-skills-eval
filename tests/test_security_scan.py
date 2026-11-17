from __future__ import annotations

from pathlib import Path

from skills_eval.security_scan import scan_skill_dir

FIXTURES = Path(__file__).parent / "fixtures"


def test_good_skill_no_security_errors() -> None:
    findings = scan_skill_dir(FIXTURES / "good_pack" / "skills" / "sample-skill")
    assert findings == []


def test_bad_skill_flags_secret_and_download_exec() -> None:
    findings = scan_skill_dir(FIXTURES / "bad_pack" / "skills" / "Broken_Name")
    codes = {f.code for f in findings}
    assert "download_exec" in codes
    assert "sk_live_token" in codes or "generic_api_key_assign" in codes
