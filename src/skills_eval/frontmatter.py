"""Minimal YAML frontmatter parser (no PyYAML dependency)."""

from __future__ import annotations

import re

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*\n", re.DOTALL)


def parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple key: value frontmatter used by Agent Skills.

    Supports folded scalars (``>`` / ``>|`` / ``>-``) and indented continuations.
    Nested keys under ``metadata:`` are not flattened; callers may regex the raw
    block for ``metadata.version``.
    """
    m = FRONTMATTER_RE.match(text)
    if not m:
        raise ValueError("missing YAML frontmatter")
    block = m.group(1)
    out: dict[str, str] = {}
    key: str | None = None
    acc: list[str] = []
    for line in block.splitlines():
        if re.match(r"^[a-zA-Z0-9_-]+:\s*", line) and not line.startswith(" "):
            if key is not None:
                out[key] = "\n".join(acc).strip().strip("\"'")
            k, _, rest = line.partition(":")
            key = k.strip()
            rest = rest.strip()
            if rest in (">|", ">"):
                acc = []
            elif rest.startswith((">-", ">")):
                acc = [rest.lstrip(">").lstrip("-").strip()]
            else:
                acc = [rest.strip("\"'")] if rest else []
        else:
            if key is not None:
                acc.append(line.strip())
    if key is not None:
        out[key] = "\n".join(acc).strip().strip("\"'")
    return out


def strip_frontmatter(text: str) -> str:
    return FRONTMATTER_RE.sub("", text, count=1)
