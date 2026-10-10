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

Otherwise the page auto-detects the browser language and remembers the visitor's
choice in `localStorage`.

---

## ⚠️ Three placeholders to replace before you share the link

Nothing else is required, but the site is not shareable until these are real.

| Where | Placeholder | Replace with |
|---|---|---|
| `index.html` — `id="rsvp-link"` | `https://forms.gle/REPLACE-WITH-YOUR-FORM` | your Google Form share link |
| `index.html` — footer | `https://wa.me/REPLACE` | `https://wa.me/84xxxxxxxxx` (no `+`, no spaces) |
| `index.html` — footer | `https://zalo.me/REPLACE` | `https://zalo.me/84xxxxxxxxx` |

Find them all at any time:

```sh
grep -n REPLACE index.html
```

---

## The RSVP form

The form is a **single bilingual Google Form**, linked out rather than embedded
(Google Forms cannot switch languages, and one form means one response sheet
instead of two to merge by hand). Suggested questions — each label carries both
languages:

1. **Tên của bạn / Your name** — short answer · *required*
2. **Bạn sẽ tham dự buổi nào? / Which celebration will you join?** — multiple choice · *required*
   - `Hà Nội — 14.11.2026`
   - `Vinh — 21.11.2026`
   - `Cả hai / Both`
   - `Rất tiếc mình không tham dự được / Sorry, I can't make it`
3. **Tổng số người tham dự, kể cả bạn / Total guests, including you** — short answer · *required*
4. **Có trẻ nhỏ không? Mấy bé? / Any children? How many?** — short answer
5. **Bạn có nhu cầu ăn đặc biệt không? (ăn chay, dị ứng…) / Any dietary needs? (vegetarian, allergies…)** — paragraph
6. **Số điện thoại hoặc Zalo / Phone or Zalo** — short answer
7. **Bạn bay từ nước ngoài về? / Travelling from abroad?** — Yes / No
8. **Lời nhắn cho chúng mình / A message for us** — paragraph

In the form's settings, turn on **Collect email addresses** only if you want it —
it adds friction for guests who are not signed in to Google.

The reply-by date shown on the site is **16 October 2026** (`rsvp.deadline` in
`assets/js/i18n.js`), about four weeks before Hanoi.

---

## Editing the words

All copy for both languages lives in one file: **`assets/js/i18n.js`**.
Each entry appears twice, once under `vi` and once under `en`:

```js
"hero.note": "Chúng mình sắp về chung một nhà — và rất mong có bạn ở đó.",
```

Change the text, save, reload. Nothing needs rebuilding. The two language blocks
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

**Our Story** is eight dated milestones (`story.i1.*` through `story.i8.*`); the
milestones that have an illustration carry it as `story.iN.alt` text. To add one,
copy an `<li>` in `index.html` and add its keys to both languages.

---

## Deploying to GitHub Pages

The site is plain static files at the repository root, so Pages needs no
configuration beyond pointing at the branch.

### The free-organisation route (gives you `chris-hallie.github.io`)

GitHub derives a root Pages URL from the **account** name, so `chris-hallie.github.io`
requires an account called `chris-hallie`. A free organisation is the clean way to
get that without a second personal login:

1. Create a free organisation named `chris-hallie`
   (github.com → **+** → **New organization** → Free).
2. Inside that org, create a repository named exactly **`chris-hallie.github.io`**.
3. Push:

   ```sh
   git remote add origin git@github.com:chris-hallie/chris-hallie.github.io.git
   git push -u origin main
   ```

4. Repo **Settings → Pages → Source: Deploy from a branch**, branch `main`, folder `/ (root)`.
5. Live at `https://chris-hallie.github.io` in a minute or two.

### Or from your own account

Push to any repo you own and enable Pages the same way. The URL becomes
`https://<your-username>.github.io/<repo-name>/`. Every asset path in this project
is **relative**, so the site works unchanged at a root domain or in a subfolder —
no base-path edits needed either way.

### A custom domain later

Worth doing before you send the link widely in Vietnam: a `github.io` URL pasted
into Zalo or Messenger looks less trustworthy than a real domain, and some link
scanners treat it more harshly.

1. Buy the domain (~$10–12/yr).
2. Add a file named `CNAME` at the repo root containing just the domain:

   ```
   chrisandhallie.com
   ```

3. At your DNS provider, point the apex at GitHub's four `A` records
   (`185.199.108.153`, `.109.153`, `.110.153`, `.111.153`) and add a `CNAME`
   for `www` → `chris-hallie.github.io`.
4. Settings → Pages → **Enforce HTTPS**.

Then update the `og:image` tags in `index.html` to absolute URLs — several chat
apps and scrapers will not resolve a relative image path:

```html
<meta property="og:image" content="https://chrisandhallie.com/assets/og/share-1200x630.png">
```

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

## Still to fill in

- [ ] Google Form link, WhatsApp number, Zalo number (see above)
- [ ] Hotel suggestions near each venue (`tr.p3.body`)
- [ ] Buy a domain before the wide send in Vietnam
