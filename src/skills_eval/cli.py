"""CLI entry: ``dup-skills-eval`` / ``python -m skills_eval``."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from skills_eval import __version__
from skills_eval.report import print_summary, write_json, write_markdown
from skills_eval.runner import evaluate_pack


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dup-skills-eval",
        description=(
            "Fail-closed industrial evaluation gate for Agent Skills packs "
            "(static + security + honesty)."
        ),
    )
    p.add_argument(
        "pack_root",
        type=Path,
        help="Path to skills pack root (contains skills/)",
    )
    p.add_argument(
        "--skills-subdir",
        default="skills",
        help="Skills subdirectory name (default: skills)",
    )
    p.add_argument(
        "--report-dir",
        type=Path,
        default=None,
        help="Write report.json + report.md here (default: <pack>/reports/skills-eval)",
    )
    p.add_argument("--no-report", action="store_true", help="Do not write report files")
    p.add_argument("--skip-security", action="store_true", help="Skip security scan")
    p.add_argument("--skip-honesty", action="store_true", help="Skip honesty/policy gate")
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    pack_root: Path = args.pack_root
    if not pack_root.exists():
        print(f"FAIL: pack root does not exist: {pack_root}", file=sys.stderr)
        return 2

    report = evaluate_pack(
        pack_root,
        skills_subdir=args.skills_subdir,
        skip_security=args.skip_security,
        skip_honesty=args.skip_honesty,
    )
    print_summary(report)

    if not args.no_report:
        out = args.report_dir
        if out is None:
            out = pack_root.resolve() / "reports" / "skills-eval"
        write_json(report, out / "report.json")
        write_markdown(report, out / "report.md")
        print(f"report: {out / 'report.json'}")
        print(f"report: {out / 'report.md'}")

    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
