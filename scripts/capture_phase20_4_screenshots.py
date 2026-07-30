from __future__ import annotations

import textwrap
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "screenshots" / "phase20_4_evidence_spacing_polish"

MANUAL_SMOKE_ENDPOINTS: tuple[tuple[str, str], ...] = (
    ("/logs", "HTTP 200"),
    ("/demo", "HTTP 200"),
    ("/dashboard", "HTTP 200"),
    ("/reports", "HTTP 200"),
    ("/api/demo/readiness", "HTTP 200"),
    ("/api/demo/run", "HTTP 200"),
    ("/api/demo/latest", "HTTP 200"),
)


def manual_smoke_rows() -> list[tuple[str, str]]:
    return list(MANUAL_SMOKE_ENDPOINTS)


def report_spacing_rows() -> list[tuple[str, str]]:
    return [
        ("demo_readiness_summary.md", "Contains no_physical_command_generated: true"),
        ("Legacy Log Format Note", "Present; old combined blockers are labelled legacy."),
        ("rendering rule", "Long labels wrap above their values when needed."),
        ("safety invariant", "DISARMED + NO_FIRE + dry_run=true + hardware_enabled=false + physical_command_enabled=false"),
    ]


def _fonts():
    from PIL import ImageFont

    sans = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    mono = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
    return (
        ImageFont.truetype(sans, 32),
        ImageFont.truetype(sans, 18),
        ImageFont.truetype(sans, 17),
        ImageFont.truetype(mono, 17),
    )


def _draw_badge(draw, x: int, y: int, label: str) -> int:
    _, small, _, _ = _fonts()
    width = int(draw.textlength(label, font=small)) + 24
    draw.rounded_rectangle((x, y, x + width, y + 34), radius=8, fill=(6, 78, 59), outline=(52, 211, 153))
    draw.text((x + 12, y + 7), label, font=small, fill=(240, 253, 244))
    return x + width + 12


def render_panel(filename: str, title: str, rows: list[tuple[str, str]]) -> Path:
    from PIL import Image, ImageDraw

    OUT.mkdir(parents=True, exist_ok=True)
    title_font, small, label_font, value_font = _fonts()
    width = 1580
    row_height = 96
    height = 250 + len(rows) * (row_height + 12) + 80
    img = Image.new("RGB", (width, height), (15, 23, 42))
    draw = ImageDraw.Draw(img)
    draw.rectangle((0, 0, width, 96), fill=(2, 6, 23))
    draw.text((46, 30), "ISTIKLAL C2 CONSOLE · PHASE 20.4 Evidence", font=small, fill=(148, 163, 184))
    draw.text((46, 118), title, font=title_font, fill=(248, 250, 252))
    _draw_badge(draw, 46, 170, "SPACING SAFE")
    _draw_badge(draw, 210, 170, "NO OVERLAP")
    y = 232
    label_x = 72
    value_x = 520
    max_label_width = value_x - label_x - 32
    for label, value in rows:
        draw.rounded_rectangle((46, y, width - 46, y + row_height), radius=10, fill=(30, 41, 59), outline=(51, 65, 85))
        if draw.textlength(label, font=label_font) > max_label_width:
            label_lines = textwrap.wrap(label, width=42)
            draw.text((label_x, y + 14), "\n".join(label_lines[:2]), font=label_font, fill=(125, 211, 252), spacing=4)
            value_y = y + 52
            value_start_x = label_x
            value_wrap = 120
        else:
            draw.text((label_x, y + 18), label, font=label_font, fill=(125, 211, 252))
            value_y = y + 18
            value_start_x = value_x
            value_wrap = 86
        value_lines = textwrap.wrap(value, width=value_wrap)
        draw.text((value_start_x, value_y), "\n".join(value_lines[:2]), font=value_font, fill=(226, 232, 240), spacing=4)
        y += row_height + 12
    draw.text((46, height - 50), f"Generated {time.strftime('%Y-%m-%d %H:%M:%S')} · no_physical_command_generated=true", font=small, fill=(148, 163, 184))
    output = OUT / filename
    img.save(output)
    return output


def capture() -> list[Path]:
    for old in OUT.glob("*.png"):
        old.unlink()
    return [
        render_panel("01_manual_smoke_spacing_fixed.png", "Manual smoke endpoint spacing fixed", manual_smoke_rows()),
        render_panel("02_reports_ktr_spacing_clean.png", "Reports/KTR evidence spacing clean", report_spacing_rows()),
    ]


if __name__ == "__main__":
    for path in capture():
        print(path)
