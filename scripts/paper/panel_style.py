import os
"""A single typographic floor for every panel that goes into a deck.

The requirement is that no text is smaller than 12 pt *as placed on the slide*. A figure
drawn at one size and shrunk by PowerPoint loses font size in proportion, so the only way
to hold the floor is to draw each panel at exactly the width it will occupy and set the
fonts to the floor at that size. Nothing here scales anything afterwards.

MIN_PT is the floor. The smaller sizes below it are deliberate exceptions and there are
none: tick labels, axis labels, titles, legends and annotations are all at or above it.
Making the panel smaller therefore removes content, not type, which is the intended
trade: a panel that has to be read at 8 pt is not a panel, it is a thumbnail.
"""

# The floor, 12 pt for a journal figure. A poster is read from two metres away and its
# body text is 17 to 28 pt, so a panel drawn at 12 pt sits below everything around it.
# PANEL_MIN_PT overrides the floor for a poster build; the figure builds never set it, so
# the journal figures are untouched.
MIN_PT = float(os.environ.get("PANEL_MIN_PT", 12.0))


def apply(plt, font_family: str) -> None:
    plt.rcParams.update({
        "font.family": font_family,
        "font.size": MIN_PT,
        "axes.labelsize": MIN_PT,
        "axes.titlesize": MIN_PT,
        "xtick.labelsize": MIN_PT,
        "ytick.labelsize": MIN_PT,
        "legend.fontsize": MIN_PT,
        "figure.titlesize": MIN_PT,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "figure.dpi": 300,
        "savefig.bbox": "tight",
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "axes.linewidth": 0.9,
        "xtick.major.width": 0.9,
        "ytick.major.width": 0.9,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
    })
