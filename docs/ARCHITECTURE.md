# Architecture — dup-skills-eval

**Org:** DUP Labs · **Product:** industrial Agent Skills evaluation gate  
**Related pack:** [`dup-agent-skills`](https://github.com/Gruver87/dup-agent-skills)

## Purpose

Fail-closed CI/ops gate for Agent Skills packs. Inspired by the 2026 SkillEvaluator
wave (static + security + task eval), scoped to **deterministic** gates first.

This tool does **not** claim live-agent PASS, 48h soak, or mainnet readiness.

## Gates (v0.1)

| Gate | Module | Fail on |
|------|--------|---------|
| Static | `static_gate.py` | agentskills naming, frontmatter, pin mismatch, missing mirror |
| Security | `security_scan.py` | secret heuristics, download-and-execute |
| Honesty | `honesty_gate.py` | obsolete repo URLs, futures-enable without refuse, missing no-futures policy |

Warnings (body length, soak wording with weak framing, missing skill but needle present)
do **not** fail the process exit code.

## Layout

```text
pack_root/
  skills/<name>/SKILL.md
  plugin.json                 # optional pin
  .agents/skills/…            # optional mirror
  packages/radar_mcp/…        # optional version pin (dup-agent-skills)
```

CLI:

```text
dup-skills-eval <pack_root> [--report-dir DIR]
```

Exit `0` only when `error_count == 0`.

## Out of scope (v0.1)

- Live multi-agent task harness (NVIDIA-style runtime scorecards)
- Network fetches / marketplace installs
- Futures / order execution of any kind

Those belong in a later version with sealed evidence packs — not silent green.
