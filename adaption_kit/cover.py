"""cover.py - render an HTML cover to PNG for a dataset/model release.

Uses Playwright (Chromium) when installed to screenshot the HTML at a fixed
viewport. When Playwright is absent it writes the HTML next to the requested PNG
and returns a result explaining how to enable rendering, so the command never
hard-fails just because an optional dependency is missing.

    pip install adaption-kit[cover]
    python -m playwright install chromium
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class CoverResult:
    """Outcome of generate_cover."""

    rendered: bool
    output_path: str  # the PNG if rendered, else the HTML fallback
    html_path: Optional[str] = None
    message: str = ""

    def summary(self) -> str:
        if self.rendered:
            return "cover PNG written to " + self.output_path
        return (
            "Playwright not available; wrote HTML to "
            + (self.html_path or self.output_path)
            + ". "
            + self.message
        )


def _default_cover_html(title: str, subtitle: str = "") -> str:
    """A clean built-in cover template, used when no html is supplied."""
    safe_title = _escape(title)
    safe_subtitle = _escape(subtitle)
    return (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        "html,body{margin:0;padding:0}"
        ".cover{width:1200px;height:630px;display:flex;flex-direction:column;"
        "justify-content:center;padding:80px;box-sizing:border-box;"
        "font-family:Arial,Helvetica,sans-serif;color:#0b1020;"
        "background:linear-gradient(135deg,#eef2ff 0%,#fce7f3 100%)}"
        ".tag{font-size:20px;letter-spacing:3px;text-transform:uppercase;"
        "color:#4338ca;margin-bottom:24px}"
        ".title{font-size:64px;font-weight:800;line-height:1.05;margin:0}"
        ".subtitle{font-size:28px;color:#334155;margin-top:24px}"
        ".foot{margin-top:48px;font-size:18px;color:#475569}"
        "</style></head><body><div class='cover'>"
        "<div class='tag'>Adaption Adaptive Data</div>"
        "<h1 class='title'>" + safe_title + "</h1>"
        + ("<div class='subtitle'>" + safe_subtitle + "</div>" if safe_subtitle else "")
        + "<div class='foot'>Built with adaption-kit - community, unofficial</div>"
        "</div></body></html>"
    )


def _escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def generate_cover(
    html: Optional[str],
    out_png: "str | Path",
    title: str = "Adaption dataset",
    subtitle: str = "",
    width: int = 1200,
    height: int = 630,
) -> CoverResult:
    """Render ``html`` to ``out_png`` via Playwright, or fall back to HTML.

    If ``html`` is None a built-in template using ``title``/``subtitle`` is used.
    Returns a CoverResult describing what happened.
    """
    out_path = Path(out_png)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    content = html if html is not None else _default_cover_html(title, subtitle)

    try:
        from playwright.sync_api import sync_playwright  # type: ignore
    except ImportError:
        html_path = out_path.with_suffix(".html")
        html_path.write_text(content, encoding="utf-8")
        return CoverResult(
            rendered=False,
            output_path=str(html_path),
            html_path=str(html_path),
            message=(
                "Install with 'pip install adaption-kit[cover]' then "
                "'python -m playwright install chromium' to render PNGs. "
                "You can also open the HTML and screenshot it manually."
            ),
        )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page(viewport={"width": width, "height": height})
            page.set_content(content, wait_until="networkidle")
            page.screenshot(path=str(out_path))
        finally:
            browser.close()

    return CoverResult(
        rendered=True,
        output_path=str(out_path),
        message="rendered with Playwright Chromium",
    )
