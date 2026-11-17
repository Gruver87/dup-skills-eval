#!/usr/bin/env python3
"""Render DUP Ecosystem E2E dashboard to PNG + PDF (no secrets)."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "assets"
PNG_NAME = "e2e-ecosystem-2026-11-17.png"
PDF_NAME = "e2e-ecosystem-2026-11-17.pdf"

# Dark industrial palette (readable on GitHub light/dark)
BG = (15, 18, 24)
CARD = (28, 33, 43)
BORDER = (55, 65, 82)
TEXT = (226, 232, 240)
MUTED = (148, 163, 184)
GREEN = (34, 197, 94)
AMBER = (245, 158, 11)
WHITE = (255, 255, 255)

GATES = [
    ("1", "dup-skill-security-scan", "PASS n=10 errors=0 denied=0", "0"),
    ("2", "dup-skills-eval", "PASS n=10 warns=0 pin=0.1.10", "0"),
    ("3", "dup-evidence-graph", "packs=69 · ops_ready YES · soak_48h NO", "0/1*"),
    ("4", "dup-policy-gate", "spot ALLOW · futures FUTURES_BLOCK", "0/1"),
]

REPOS = [
    ("dup-agent-skills", "Объект проверки (skills pack)"),
    ("dup-market-radar", "Evidence packs + ops_ready"),
    ("absolute-trading-bot-final", "Bot protocol status pack"),
    ("dup-skills-eval", "Gate #2 static/honesty"),
    ("dup-skill-security-scan", "Gate #1 allowlist/security"),
    ("dup-evidence-graph", "Gate #3 Desktop claim map"),
    ("dup-policy-gate", "Gate #4 order policy"),
    ("dup-radar-news-mcp", "Companion digest MCP (live ok)"),
]


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    candidates = [
        r"C:\Windows\Fonts\segoeuib.ttf" if bold else r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arialbd.ttf" if bold else r"C:\Windows\Fonts\arial.ttf",
        r"C:\Windows\Fonts\consola.ttf",
    ]
    for path in candidates:
        if Path(path).is_file():
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def _rounded(draw: ImageDraw.ImageDraw, xy: tuple[int, int, int, int], fill, radius: int = 14) -> None:
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=BORDER, width=1)


def render_png(path: Path) -> None:
    w, h = 1400, 1180
    img = Image.new("RGB", (w, h), BG)
    d = ImageDraw.Draw(img)
    title = _font(36, bold=True)
    h2 = _font(22, bold=True)
    body = _font(16)
    small = _font(14)
    mono = _font(15)

    d.text((48, 36), "DUP Ecosystem E2E — 2026-11-17", fill=WHITE, font=title)
    d.text(
        (48, 86),
        "security-scan → skills-eval → evidence-graph → policy-gate  ·  soak not run  ·  no KuCoin keys",
        fill=MUTED,
        font=small,
    )

    # Status pills
    pills = [("E2E PASS", GREEN), ("8 repos", MUTED), ("soak_48h REFUSE", AMBER), ("futures REFUSE", AMBER)]
    x = 48
    for label, color in pills:
        tw = d.textlength(label, font=small) + 28
        _rounded(d, (x, 118, int(x + tw), 148), CARD, 10)
        d.text((x + 14, 124), label, fill=color, font=small)
        x += tw + 10

    # Stats
    stats = [("4/4", "Gates green"), ("10", "Skills scanned"), ("69", "Evidence packs"), ("0", "KuCoin keys used")]
    for i, (val, lab) in enumerate(stats):
        sx = 48 + i * 330
        _rounded(d, (sx, 172, sx + 310, 262), CARD)
        d.text((sx + 20, 188), val, fill=GREEN if i == 0 else WHITE, font=title)
        d.text((sx + 20, 230), lab, fill=MUTED, font=body)

    # Verdict card
    _rounded(d, (48, 282, w - 48, 360), CARD)
    d.text(
        (68, 300),
        "Системы видят общий объект (dup-agent-skills / Desktop packs) и fail-closed:",
        fill=TEXT,
        font=body,
    )
    d.text(
        (68, 328),
        "security+eval PASS · evidence: ops_ready YES / soak NO · policy: spot ALLOW / futures REFUSE",
        fill=MUTED,
        font=small,
    )

    # Gates table header
    d.text((48, 388), "Результаты гейтов", fill=WHITE, font=h2)
    y = 430
    headers = ["#", "Система", "Результат", "Exit"]
    cols = [48, 90, 420, 1240]
    for i, head in enumerate(headers):
        d.text((cols[i], y), head, fill=MUTED, font=small)
    y = 458
    d.line((48, y, w - 48, y), fill=BORDER, width=1)
    y += 14
    for num, name, result, exit_code in GATES:
        d.text((cols[0], y), num, fill=GREEN, font=mono)
        d.text((cols[1], y), name, fill=TEXT, font=mono)
        d.text((cols[2], y), result, fill=MUTED, font=small)
        d.text((cols[3], y), exit_code, fill=GREEN if exit_code.startswith("0") else AMBER, font=mono)
        y += 34

    d.text(
        (48, y + 4),
        "* soak_48h exit=1 и futures exit=1 — ожидаемый fail-closed (не баг).",
        fill=MUTED,
        font=small,
    )

    # Repos
    y += 48
    d.text((48, y), "8 репозиториев экосистемы", fill=WHITE, font=h2)
    y += 40
    for name, role in REPOS:
        _rounded(d, (48, y, w - 48, y + 40), CARD, 8)
        d.text((64, y + 10), name, fill=GREEN, font=mono)
        d.text((420, y + 10), role, fill=TEXT, font=small)
        y += 48

    d.text(
        (48, h - 36),
        "DUP Labs · fail-closed · not financial advice · https://github.com/Gruver87/dup-skills-eval",
        fill=MUTED,
        font=small,
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    img.save(path, "PNG", optimize=True)


def render_pdf(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    c = pdfcanvas.Canvas(str(path), pagesize=A4)
    width, height = A4
    x, y = 20 * mm, height - 20 * mm

    def line(text: str, size: int = 11, dy: float = 6 * mm, bold: bool = False) -> None:
        nonlocal y
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(x, y, text)
        y -= dy

    line("DUP Ecosystem E2E — 2026-11-17", 16, 8 * mm, bold=True)
    line("security-scan → skills-eval → evidence-graph → policy-gate", 10, 5 * mm)
    line("Verdict: E2E PASS (soak not run; no KuCoin keys)", 11, 8 * mm, bold=True)
    line("Gates", 13, 7 * mm, bold=True)
    for num, name, result, exit_code in GATES:
        line(f"{num}. {name}  [{exit_code}]  {result}", 9, 5 * mm)
    y -= 3 * mm
    line("8 repositories", 13, 7 * mm, bold=True)
    for name, role in REPOS:
        line(f"- {name}: {role}", 9, 5 * mm)
    y -= 4 * mm
    line("* soak_48h / futures exit=1 are expected fail-closed refuses.", 8, 5 * mm)
    line("DUP Labs · not financial advice · github.com/Gruver87/dup-skills-eval", 8, 5 * mm)
    c.showPage()
    c.save()


def main() -> int:
    png = OUT_DIR / PNG_NAME
    pdf = OUT_DIR / PDF_NAME
    render_png(png)
    render_pdf(pdf)
    print(f"wrote {png}")
    print(f"wrote {pdf}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
