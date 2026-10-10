#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["pillow", "numpy", "scipy"]
# ///
"""Re-ground an illustration on the site's one paper colour, crop it, export WebP.

Watercolour on paper is multiplicative: pixel = paper * ink. The script measures the
paper from the border, divides it out to recover the ink, clears paper grain and drift,
erases detached caption text, then multiplies the ink onto the target paper.
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

DOWN = 4  # working scale for blurs and component labelling


def repo_root() -> Path:
    for p in Path(__file__).resolve().parents:
        if (p / "assets" / "css" / "style.css").exists():
            return p
    sys.exit("assets/css/style.css not found above the script; pass --paper")


def hex_rgb(h: str) -> np.ndarray:
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255


def default_paper() -> str:
    css = (repo_root() / "assets" / "css" / "style.css").read_text()
    m = re.search(r"--card:\s*(#[0-9a-fA-F]{6})", css)
    if not m:
        sys.exit("--card not found in style.css; pass --paper")
    return m.group(1)


def resize(a: np.ndarray, h: int, w: int, resample) -> np.ndarray:
    if a.ndim == 2:
        return np.asarray(Image.fromarray(a.astype(np.float32), "F").resize((w, h), resample))
    return np.stack([resize(a[..., c], h, w, resample) for c in range(a.shape[2])], axis=2)


def smoothstep(x: np.ndarray) -> np.ndarray:
    x = np.clip(x, 0, 1)
    return x * x * (3 - 2 * x)


def estimate_paper(img: np.ndarray, tol: float):
    """Paper colour per pixel, from border-connected pixels near the border colour."""
    h, w, _ = img.shape
    b = max(4, int(0.015 * min(h, w)))
    edge = np.concatenate([img[:b].reshape(-1, 3), img[-b:].reshape(-1, 3),
                           img[:, :b].reshape(-1, 3), img[:, -b:].reshape(-1, 3)])
    ref = np.median(edge, axis=0)
    near = np.abs(ndi.gaussian_filter(img, (1.5, 1.5, 0)) - ref).max(axis=2) < tol
    lab, _ = ndi.label(near)
    border_labels = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    mask = ndi.binary_erosion(np.isin(lab, border_labels[border_labels > 0]), iterations=2)

    hs, ws = h // DOWN, w // DOWN
    m = resize(mask.astype(np.float32), hs, ws, Image.BOX)
    im = resize(img * mask[..., None], hs, ws, Image.BOX)
    est = np.zeros((hs, ws, 3), np.float32)
    got = np.zeros((hs, ws), bool)
    for sigma in (8, 30, 100):  # normalized convolution, widening until every pixel is covered
        den = ndi.gaussian_filter(m, sigma)
        num = ndi.gaussian_filter(im, (sigma, sigma, 0))
        ok = (den > 0.02) & ~got
        est[ok] = num[ok] / den[ok, None]
        got |= ok
    est[~got] = ref
    return np.maximum(resize(est, h, w, Image.BILINEAR), 0.2), ref, mask.mean()


def split_ink(ink: np.ndarray, t0: float, t1: float, seed: float, gap: float, keep_frac: float):
    """Weight of real ink per pixel, plus the detached components to erase."""
    h, w, _ = ink.shape
    dev = np.abs(ndi.gaussian_filter(ink, (1.5, 1.5, 0)) - 1).max(axis=2)
    # hysteresis: faint regions count as ink only when they touch a strong stroke, so grain never does
    lab, _ = ndi.label(dev > t0, structure=np.ones((3, 3), bool))
    seeded = np.unique(lab[dev > seed])
    region = np.isin(lab, seeded[seeded > 0])
    weight = ndi.gaussian_filter(ndi.maximum_filter(smoothstep((dev - t0) / (t1 - t0)) * region, 5), 1.2)

    hs, ws = h // DOWN, w // DOWN
    coarse = resize((weight > 0.5).astype(np.float32), hs, ws, Image.BOX) > 0.25
    grown = ndi.binary_dilation(coarse, structure=np.ones((3, 3), bool),
                                iterations=max(1, round(gap * h / DOWN / 2)))
    lab, n = ndi.label(grown, structure=np.ones((3, 3), bool))
    ids = np.arange(1, n + 1)
    areas = np.array(ndi.sum(coarse, lab, ids))
    drop = ids[areas < keep_frac * areas.max()]
    dropped = []
    for i in drop:
        ys, xs = np.where(lab == i)
        if coarse[lab == i].any():
            dropped.append((xs.min() * DOWN, ys.min() * DOWN, (xs.max() + 1) * DOWN,
                            (ys.max() + 1) * DOWN, areas[i - 1] / areas.max()))
    drop_full = resize(np.isin(lab, drop).astype(np.float32), h, w, Image.NEAREST) > 0.5
    return weight, drop_full, dropped


def window(bbox, aspect: float, margin: float):
    x0, y0, x1, y1 = bbox
    wh = max((y1 - y0) * (1 + 2 * margin), (x1 - x0) * (1 + 2 * margin) / aspect)
    ww = wh * aspect
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return round(cx - ww / 2), round(cy - wh / 2), round(cx + ww / 2), round(cy + wh / 2)


def crop_on_paper(a: np.ndarray, win, paper: np.ndarray) -> np.ndarray:
    wx0, wy0, wx1, wy1 = win
    out = np.empty((wy1 - wy0, wx1 - wx0, 3), np.float32)
    out[:] = paper
    h, w, _ = a.shape
    sx0, sy0, sx1, sy1 = max(wx0, 0), max(wy0, 0), min(wx1, w), min(wy1, h)
    out[sy0 - wy0:sy1 - wy0, sx0 - wx0:sx1 - wx0] = a[sy0:sy1, sx0:sx1]
    return out


def to_u8(a: np.ndarray) -> Image.Image:
    return Image.fromarray(np.clip(a * 255 + 0.5, 0, 255).astype(np.uint8))


def bg_check(path: Path, paper: np.ndarray) -> float:
    a = np.asarray(Image.open(path).convert("RGB")).astype(float)
    h, w, _ = a.shape
    s = 8
    spots = [a[:s, :s], a[:s, -s:], a[-s:, :s], a[-s:, -s:],
             a[:s, w // 2 - s:w // 2 + s], a[-s:, w // 2 - s:w // 2 + s]]
    return max(float(np.abs(np.median(p.reshape(-1, 3), axis=0) - paper * 255).max()) for p in spots)


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("src", type=Path, help="source image (PNG/JPG/WebP)")
    ap.add_argument("--name", required=True, help="output stem, e.g. couple_window")
    ap.add_argument("--out", type=Path, help="output dir (default: <repo>/assets/art)")
    ap.add_argument("--paper", help="target paper hex (default: --card in style.css)")
    ap.add_argument("--aspect", default="3:4", help="crop window W:H (default 3:4)")
    ap.add_argument("--margin", type=float, default=0.12, help="paper around the subject, fraction of its size")
    ap.add_argument("--widths", default="460,700",
                    help="comma-separated output widths, capped at the window's native width")
    ap.add_argument("--quality", type=int, default=82)
    ap.add_argument("--keep-captions", action="store_true", help="keep detached small components")
    ap.add_argument("--gap", type=float, default=0.035,
                    help="blank gap (fraction of height) that separates a caption from the subject")
    ap.add_argument("--keep-frac", type=float, default=0.05,
                    help="components smaller than this fraction of the largest are captions")
    ap.add_argument("--paper-tol", type=float, default=0.045, help="border-colour tolerance for finding bare paper")
    ap.add_argument("--ink-lo", type=float, default=0.03, help="deviation from paper below which a pixel is bare paper")
    ap.add_argument("--ink-hi", type=float, default=0.06, help="deviation from paper above which a pixel is fully ink")
    ap.add_argument("--ink-seed", type=float, default=0.12,
                    help="a faint region is ink only if it holds a pixel this far from paper")
    ap.add_argument("--preview-dir", type=Path, help="default: <repo>/.tmp/art-preview")
    args = ap.parse_args()

    root = repo_root()
    out_dir = args.out or root / "assets" / "art"
    preview_dir = args.preview_dir or root / ".tmp" / "art-preview"
    paper = hex_rgb(args.paper or default_paper())
    aw, ah = (float(v) for v in args.aspect.split(":"))
    aspect = aw / ah

    src = Image.open(args.src).convert("RGB")
    img = np.asarray(src).astype(np.float32) / 255
    h, w, _ = img.shape

    est, ref, paper_cover = estimate_paper(img, args.paper_tol)
    ink = img / est
    weight, drop_full, dropped = split_ink(ink, args.ink_lo, args.ink_hi, args.ink_seed, args.gap, args.keep_frac)
    if args.keep_captions:
        drop_full[:] = False
        dropped = []
    weight = np.where(drop_full, 0, weight)
    result = np.clip(paper * (1 + (ink - 1) * weight[..., None]), 0, 1)

    ys, xs = np.where(weight > 0.5)
    if len(xs) == 0:
        sys.exit("no ink found; lower --ink-lo / --paper-tol")
    bbox = (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)
    win = window(bbox, aspect, args.margin)
    framed = crop_on_paper(result, win, paper)
    native_w = framed.shape[1]
    padded = max(0, -win[0], -win[1], win[2] - w, win[3] - h)

    out_dir.mkdir(parents=True, exist_ok=True)
    widths = sorted({min(int(v), native_w) for v in args.widths.split(",")})
    written = []
    for tw in widths:
        th = round(tw / aspect)
        im = to_u8(framed).resize((tw, th), Image.LANCZOS)
        path = out_dir / f"{args.name}-{tw}.webp"
        im.save(path, "WEBP", quality=args.quality, method=6)
        written.append((tw, th, path))

    preview_dir.mkdir(parents=True, exist_ok=True)
    before = src.copy()
    d = ImageDraw.Draw(before)
    for x0, y0, x1, y1, _ in dropped:
        d.rectangle((x0, y0, x1, y1), outline=(220, 0, 0), width=4)
    d.rectangle(win, outline=(0, 160, 0), width=4)
    ph = 640
    left = before.resize((round(w * ph / h), ph))
    right = to_u8(framed).resize((round(framed.shape[1] * ph / framed.shape[0]), ph))
    sheet = Image.new("RGB", (left.width + right.width + 30, ph), (120, 120, 120))
    sheet.paste(left, (0, 0))
    sheet.paste(right, (left.width + 30, 0))
    sheet.save(preview_dir / f"{args.name}.png")

    def rel(p: Path) -> Path:
        return p.relative_to(root) if p.is_relative_to(root) else p

    def rgb(c: np.ndarray) -> tuple:
        return tuple(int(v) for v in (c * 255).round())

    print(f"source        {args.src.name} {w}x{h}")
    print(f"paper found   {rgb(ref)} ({paper_cover:.0%} of frame) -> {rgb(paper)}")
    print(f"captions      {len(dropped)} erased" + "".join(
        f"\n  - box {x0},{y0}-{x1},{y1}  ({f:.1%} of subject)" for x0, y0, x1, y1, f in dropped))
    print(f"window        {win} ({'padded with paper ' + str(padded) + 'px' if padded else 'inside source'})")
    for tw, th, path in written:
        print(f"wrote         {rel(path)} {tw}x{th}  bg-check max dev {bg_check(path, paper):.1f}/255")
    big = written[-1]
    srcset = ", ".join(f"{rel(p).as_posix()} {tw}w" for tw, _, p in written)
    print(f'html          src="{rel(big[2]).as_posix()}" srcset="{srcset}" width="{big[0]}" height="{big[1]}"')
    print(f"preview       {rel(preview_dir / (args.name + '.png'))}"
          "  (left: source, red = erased, green = window; right: result)")


if __name__ == "__main__":
    main()
