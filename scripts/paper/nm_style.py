"""Nature Methods figure spec, as constants. Verified 2026-10-01 from
nature.com/documents/nature-final-artwork.pdf and nature.com/nmeth/content.

  widths        89 mm single column, 183 mm double column (120 or 136 mm for 1.5)
  page depth    247 mm
  typeface      sans-serif, Helvetica or Arial
  panel letters 8 pt bold, upright, lowercase a, b, c
  other text    5 pt minimum, 7 pt MAXIMUM
  text          editable vector, never rasterised or outlined
  formats       AI, EPS, PDF, PowerPoint; not PNG, TIFF, JPEG

The decks are built at 183 mm (7.20 in) wide, so what is on the slide is what prints.
LEGACY_W is the 13.33 in canvas the first frameworks were laid out on; SCALE maps those
layout constants onto the Nature page.
"""
MM = 1 / 25.4
PAGE_W = 183 * MM            # 7.205 in, double column
PAGE_W_SINGLE = 89 * MM      # 3.504 in
PAGE_DEPTH = 247 * MM        # 9.724 in, the whole page; the legend needs some of it
PT_TEXT = 7.0                # every run of text that is not a panel letter
PT_LABEL = 8.0               # panel letters, bold lowercase
PT_MIN = 5.0
FONT = "Arial"

LEGACY_W = 13.333
SCALE = PAGE_W / LEGACY_W    # 0.5404


def s(v: float) -> float:
    """A layout length tuned on the 13.33 in canvas, on the 183 mm page."""
    return v * SCALE
