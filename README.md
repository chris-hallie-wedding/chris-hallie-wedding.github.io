# Khánh & Hường · Chris & Hallie — wedding site

A bilingual (Vietnamese / English) one-page wedding invitation for two celebrations:

| | Hanoi | Vinh |
|---|---|---|
| Date | Saturday 14 November 2026 | Saturday 21 November 2026 |
| Lunar | 06/10 Bính Ngọ | 13/10 Bính Ngọ |
| Time | 11:00 | 11:00 |
| Venue | MIPEC Palace, Tầng 5 | Diamond Palace, Sảnh 2 – Tầng 1 |
| Address | 229 Tây Sơn, P. Kim Liên, Hà Nội | Khách sạn Giao Tế, 9 Hồ Tùng Mậu, P. Thành Vinh, Nghệ An |

No build step, no dependencies, no framework. Three files do the work:
`index.html`, `assets/css/style.css`, `assets/js/i18n.js` (+ `app.js`).

---

## Preview locally

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

Open it through a server rather than double-clicking the file — `file://` blocks
webfont loading, so the script faces will silently fall back.

Force a language with a query parameter:

- `http://localhost:8000/?lang=vi`
- `http://localhost:8000/?lang=en`

Otherwise the page opens in English and remembers the visitor's choice in
`localStorage`. Send Vietnamese guests `https://chris-hallie-wedding.github.io/?lang=vi`.

---

## Links and contacts

All set — nothing is left as a placeholder.

| Where | Value |
|---|---|
| `index.html` — `id="rsvp-link"` | `https://forms.gle/4wtDC4QDsTf2Fm3j8` (the Google Form) |
| `index.html` — footer `.contact` | `mailto:` links for `tranduckhanh96@gmail.com` and `daothuhuong96@gmail.com` |

To change the form, swap the `href` on `#rsvp-link`. The footer's lead-in text is
`foot.ask` in `assets/js/i18n.js`.

---

## The RSVP form

The form is a **single English-only Google Form**, linked out rather than embedded
(one form means one response sheet instead of two to merge by hand). The site's
RSVP note tells Vietnamese guests they can answer in Vietnamese. Questions:

1. **Your name** — short answer · *required*
2. **Which celebration will you join?** — multiple choice · *required*
   - `Hanoi — 14 November 2026`
   - `Vinh — 21 November 2026`
   - `Both`
   - `Sorry, I can't make it`
3. **Total guests, including you** — short answer · *required*
4. **Any children? How many?** — short answer
5. **Any dietary needs? (vegetarian, allergies…)** — paragraph
6. **Phone or Zalo** — short answer
7. **Travelling from abroad?** — Yes / No
8. **A message for us** — paragraph

In the form's settings, turn on **Collect email addresses** only if you want it —
it adds friction for guests who are not signed in to Google.

The reply-by date shown on the site is **23 October 2026** (`rsvp.deadline` in
`assets/js/i18n.js`), three weeks before Hanoi. Google Forms will not close itself
on that date — turn off **Accepting responses** by hand when you are done.

---

## Editing the words

All copy for both languages lives in one file: **`assets/js/i18n.js`**.
Each entry appears twice, once under `vi` and once under `en`:

```js
"hero.note": "Chúng mình sắp về chung một nhà — và rất mong có bạn ở đó.",
```

Change the text, save, reload. Nothing needs rebuilding. The tab title is
`meta.title`. `index.html` also carries the English text as a no-JavaScript
fallback, so when you change an `en` entry, mirror it there too. The two language blocks
must keep the same set of keys — this checks that they do:

```sh
node -e '
global.window={}; require("./assets/js/i18n.js");
const {vi,en}=window.I18N, k=Object.keys;
console.log("vi",k(vi).length,"en",k(en).length);
console.log("only in vi:", k(vi).filter(x=>!(x in en)));
console.log("only in en:", k(en).filter(x=>!(x in vi)));
'
```

**Our Story** is seven dated milestones (`story.i1.*` through `story.i7.*`); the
milestones that have an illustration carry it as `story.iN.alt` text. To add one,
copy an `<li>` in `index.html` and add its keys to both languages.

On phones (≤ 560px) the photo gallery (`.gal`) and any milestone with more than one
illustration (`.tl-art` without `.tl-art-solo`) become sideways-swipe rows with
scroll snapping instead of stacking — see the media query in `assets/css/style.css`.

---

## Deploying to GitHub Pages

The site is plain static files at the repository root, so Pages needs no
configuration beyond pointing at the branch.

It lives in the free organisation **`chris-hallie-wedding`**, repository
**`chris-hallie-wedding.github.io`**, which gives the root URL
**https://chris-hallie-wedding.github.io/**.

1. Push to `main`:

   ```sh
   git push origin main
   ```

2. Repo **Settings → Pages → Source: Deploy from a branch**, branch `main`, folder `/ (root)`
   (one-time setup).
3. Changes go live in a minute or two.

The canonical link, `og:url`, `og:image` and `twitter:image` in `index.html` use
absolute `https://chris-hallie-wedding.github.io/...` URLs, because several chat
apps and scrapers will not resolve a relative image path. Other asset paths are
relative, so the site also works locally or in a subfolder.

### A custom domain later (optional)

1. Buy the domain (~$10–12/yr).
2. Add a file named `CNAME` at the repo root containing just the domain:

   ```
   chrisandhallie.com
   ```

3. At your DNS provider, point the apex at GitHub's four `A` records
   (`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`) and add a `CNAME`
   for `www` → `chris-hallie-wedding.github.io`.
4. Settings → Pages → **Enforce HTTPS**.
5. Replace `https://chris-hallie-wedding.github.io/` with the new domain in the
   canonical, `og:url`, `og:image` and `twitter:image` tags of `index.html`.

---

## How the artwork was prepared

Source illustrations live in `.tmp/` (git-ignored — they are working files, not
part of the site). The published assets in `assets/art/` are derived from them by
the `normalize-art-background` skill (`.agents/skills/normalize-art-background/`).
Run it on every new illustration so the grounds stay uniform:

```sh
uv run .agents/skills/normalize-art-background/scripts/normalize_art.py ".tmp/images/<src>.png" --name <stem>
```

- **One paper for every illustration.** The sources came with different grounds —
  clean cream, grey-beige, peach. Watercolour is paper × ink, so the script measures
  each source's paper, divides it out, and multiplies the ink onto `--card`
  (`#FBF8F1`). Tiles and the hero then share one ground, seamless inside the
  `.framed` card, with no alpha channel.
- **Captions erased.** Three illustrations had text painted into the artwork
  (`together 2024`, `OUR DAY 2024`, `PERFECT FIT`). The `2024` contradicted a 2026
  wedding and the English text would not translate, so the script erases small
  components separated from the subject and the captions are re-set as real HTML
  text instead — translatable, restylable, and correct.
- **Cropped by ink detection**, not by eye: the subject's bounding box comes from
  pixels that carry real ink (paper grain ignored) plus a fixed margin, in a 3:4
  window (hero 862:1047). A window reaching past the source is padded with paper.
- **Converted to WebP** at two or three widths each with `srcset`.
  **16.3 MB of PNG became under 1 MB** — this matters on Vietnamese mobile data.
- **`assets/og/`** holds the composed share cards: 1200×630 for most apps and
  1200×1200 because Zalo and some chat clients prefer square and crop 1.91:1 badly.
  Both were built by extending the cream field sideways rather than cropping the
  figures.

One illustration was deliberately left out: the cats on the SpongeBob towel, whose
saturated blue and yellow sit outside the cream-and-gold palette.

## Design tokens

Sampled from the printed invitation rather than guessed — gold `#CC9C66` was the
dominant ink across the frame and script on the Hanoi print.

| Token | Value | Use |
|---|---|---|
| `--cream` | `#F4F0E4` | page |
| `--cream-alt` | `#EFEADB` | alternating sections |
| `--card` | `#FBF8F1` | framed cards |
| `--gold` | `#CC9C66` | frames, script names, accents |
| `--ink` | `#2E2A26` | body text |

Type: **Allura** for names, **Cormorant Garamond** for dates and numerals,
**Quicksand** for body and UI. Every face was verified to carry the full Vietnamese
glyph set — `Trần Đức Khánh` and `Đào Thu Hường` render in one typeface with no
mid-word fallback. Fonts that declare no Vietnamese subset were ruled out during
selection (Parisienne, Sacramento, Tangerine, Libre Baskerville and others).

---

## Still to do

- [x] Google Form link and contact emails
- [x] Hotels — `tr.p3.body` now asks guests to contact you for suggestions
- [x] Publish at https://chris-hallie-wedding.github.io/ with absolute share URLs
