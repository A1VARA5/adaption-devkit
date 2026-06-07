# Dataset cover

`cover.html` is a brandless dark cover at 1200x630, the standard social and Hugging Face card size.
It is generic so anyone can reuse it. Community, unofficial, Apache-2.0.

## Customize

Open `cover.html` and replace the PLACEHOLDER text:

- `PLACEHOLDER EYEBROW`: a short kicker, for example DATASET or MODEL or the domain.
- `PLACEHOLDER Title Goes Here`: the main title.
- `PLACEHOLDER subtitle`: one line of description.
- Stat tiles: keep up to four, delete the `<div class="tile">` blocks you do not need. Each tile has
  a `value` and a `label`, for example a row count, a language, a format, or an improvement percent.

Colors live in the `:root` block at the top of the file if you want to retune the dark theme or the
accent.

## Render to PNG

The HTML is self-contained, so any HTML-to-image tool works. Two options:

### Playwright (recommended, exact 1200x630)

```bash
pip install playwright
playwright install chromium
```

```python
from playwright.sync_api import sync_playwright
from pathlib import Path

html = Path("cover.html").resolve().as_uri()
with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page(viewport={"width": 1200, "height": 630})
    page.goto(html)
    page.screenshot(path="cover.png")
    browser.close()
```

### Headless Chrome or Edge

```bash
chrome --headless --screenshot=cover.png --window-size=1200,630 --default-background-color=00000000 cover.html
```

On Windows substitute the Edge or Chrome executable path. Confirm the output is exactly 1200x630
before uploading.

## Use it

Upload `cover.png` as the dataset or model card image on Hugging Face, and as the cover image on
Kaggle. A cover plus a filled-in card is what makes a release look complete.
