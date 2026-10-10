---
name: normalize-art-background
description: Normalize illustration backgrounds onto the site's one paper colour, erase painted captions, crop, export WebP. Use when adding or replacing artwork in assets/art, or when tiles show mismatched grounds.
---

# Normalize art background

Every illustration sits on the same **paper**: `--card` in `assets/css/style.css` (read at run time). Watercolour is multiplicative (pixel = paper × ink), so `normalize_art.py` measures the source's own paper from its border, divides it out, clears grain and drift, then multiplies the ink onto the target paper. Gallery tiles and the hero (inside `.framed`, also `--card`) end up on one seamless ground, with no alpha.

## Steps

1. **Start from the original.** Keep the source PNG under `.tmp/` (git-ignored, e.g. `.tmp/images/` or a batch folder like `.tmp/new-arts/`). Re-processing a file from `assets/art/` stacks lossy WebP on lossy WebP. Name the output stem after the file (`move-in-our-first-house.png` becomes `move_in_our_first_house`).
2. **Run** (uv installs the dependencies):

   ```sh
   uv run .agents/skills/normalize-art-background/scripts/normalize_art.py ".tmp/images/<src>.png" --name <stem>
   ```

   Defaults: 3:4 window, widths 460 and 700 (capped at the window's native width), output to `assets/art/`. Hero art: `--aspect 862:1047 --widths 460,700,1000`. Wide subjects shown solo (the timeline cats): `--aspect 4:3`. Other flags: `--help`.

3. **Review** `.tmp/art-preview/<stem>.png` (left source, right result). Done when every red box is a caption or watermark, the green window holds the whole subject, and the result shows no grain speckle or halo. Fix by flag:
   - caption survives: raise `--gap`
   - real artwork erased: raise `--gap`, lower `--keep-frac`, or pass `--keep-captions`
   - faint wash lost: lower `--ink-seed` or `--ink-lo`
   - speckle in the paper: raise `--ink-seed` or `--ink-lo`
4. **Check the report.** Done when `bg-check` is at most 2/255 for every width and `paper found` covers at least 50% of the frame; a smaller share means the subject reaches the border and the paper estimate is unreliable.
5. **Wire it into `index.html`.** Copy `src`, `srcset`, `width`, `height` from the printed `html` line; keep `sizes`, `loading` and the `data-i18n-attr` alt. Set captions as translatable HTML text, never in the art.

## Why these choices

- The paper is estimated from border-connected pixels, so a source with drifting or tinted paper (the peach cat blanket, the grey cat box) lands on the same ground as clean ones.
- Ink counts only where a faint region touches a strong stroke (hysteresis), so paper grain never becomes artwork.
- A caption is a small component separated from the subject by a blank gap; it is erased, not cropped, so the window can sit on the subject.
- Windows that reach past the source are padded with paper, which is invisible once the ground is uniform.
