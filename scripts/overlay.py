"""Shared drawing helpers for the tracking GIFs (04_make_previews.py, 06_side_by_side_gif.py).

Colours: one fixed random colour per lineage id (seeded, so every GIF uses the same colours);
0 = background (not drawn), 1 = untracked objects (grey).
GIF frames are mapped onto a fixed palette (64 grey levels + every lineage colour + magenta) instead of
automatic colour reduction, which otherwise spends the 256 GIF colours on grey and washes out outlines.
"""
import numpy as np
from PIL import Image
from scipy import ndimage
from skimage.segmentation import find_boundaries

MAGENTA = (255, 0, 255)
N_GRAYS = 64


def lineage_colours(n_ids, seed=0):
    colours = np.random.default_rng(seed).uniform(0.25, 1.0, size=(n_ids + 1, 3))
    colours[0] = 0
    colours[1] = 0.45
    return colours


def gif_palette(colours):
    """A 'P'-mode image holding the fixed GIF palette (<= 256 entries)."""
    grays = [(g, g, g) for g in np.linspace(0, 255, N_GRAYS).astype(int)]
    entries = grays + [tuple(int(v) for v in c) for c in (colours[1:] * 255).round()] + [MAGENTA]
    assert len(entries) <= 256, "too many lineages for one GIF palette"
    flat = [v for rgb in entries for v in rgb]
    pal = Image.new("P", (1, 1))
    pal.putpalette(flat + [0] * (768 - len(flat)))
    return pal


def contrast_limits(raw):
    """1st and 99.8th percentile of the movie's brightness (sampled every 4th frame/pixel)."""
    return np.percentile(raw[::4, ::4, ::4, 0], [1, 99.8])


def overlay(gray, labels, colours, size):
    """Contrast-stretched frame at display `size` (w, h) with 2-px lineage outlines in their colours.

    gray: frame scaled to 0..1, labels: lineage ids, both (y, x) at full resolution.
    """
    w, h = size
    img = np.asarray(Image.fromarray((gray * 255).astype(np.uint8)).resize((w, h), Image.BILINEAR))
    small = np.asarray(Image.fromarray(labels.astype(np.int32)).resize((w, h), Image.NEAREST))
    edge = ndimage.binary_dilation(find_boundaries(small, mode="inner")) & (small > 0)
    # Dilation can push an outline onto background; give those pixels the neighbouring object's id.
    grown = ndimage.grey_dilation(small, size=3)
    ids = np.where(small > 0, small, grown)
    rgb = np.repeat(img[..., None], 3, axis=2)
    rgb[edge] = (colours[ids[edge]] * 255).astype(np.uint8)
    return Image.fromarray(rgb)


def to_gif_frame(image, palette):
    return image.convert("RGB").quantize(palette=palette, dither=Image.Dither.NONE)
