# Climb Log

A personal map of climbing & bouldering gyms across the Netherlands, Belgium,
and the sliver of Germany around Limburg (Aachen) — like a "places I've
travelled" map, but for gyms and sessions.

Each gym is a markdown file with a bit of frontmatter. A small build script
compiles all of them into one JSON file that a [Leaflet](https://leafletjs.com/)
map reads. No database, no backend — just markdown, committed to git.

**[Live demo →](#)** *(update this link once GitHub Pages is enabled — see below)*

## How it works

```
gyms/*.md  →  scripts/build.js  →  data/gyms.json  →  index.html + js/map.js
```

- `gyms/*.md` — one file per gym. You edit these.
- `scripts/build.js` — reads every file in `gyms/`, validates it, and writes
  `data/gyms.json`. No npm dependencies required.
- `index.html` / `css/style.css` / `js/map.js` — the static site. Fetches
  `data/gyms.json` and renders the map, sidebar list, stats, and filters.
- `.github/workflows/deploy.yml` — on every push to `main`, runs the build
  script and publishes the result to GitHub Pages.

## Logging a gym

Add a new file to `gyms/`, e.g. `gyms/base-camp-maastricht.md`:

```markdown
---
name: "Base Camp Maastricht"
city: "Maastricht"
country: "NL"
lat: 50.8514
lon: 5.6910
discipline: ["boulder", "toprope"]   # any of: boulder, toprope, lead
visited: true
checked: true       # you've confirmed name/address/coords against the gym's own website
rating: 4          # optional, 1-5
website: "https://example.com"       # optional
lastVisit: "2026-08-01"              # optional, used for the trail line & sorting
---
Whatever you want to remember: the vibe, the route setting, who you went
with, that one green boulder you finally sent.
```

- **`discipline`** — list every style you've climbed there. This drives
  both the marker colour and the sidebar filter chips.
- **`visited: false`** — use this for gyms you know about but haven't been
  to yet; they still show on the map, greyed out, as a to-do list.
- **`checked`** — independent of `visited`. Set to `true` once you've
  confirmed the name, address, and coordinates against the gym's own
  website (as opposed to a directory listing that might be stale or
  slightly off). Checked gyms get a small ✓ badge in the list and popup,
  and there's a "Verified only" filter chip to spot the ones you still
  need to double-check. Defaults to `false` if omitted.
- Coordinates: right-click a spot on [Google Maps](https://maps.google.com)
  or [OpenStreetMap](https://www.openstreetmap.org) and copy the lat/lon.
- The **markdown body** becomes your notes — shown in the popup on the map.

Then rebuild locally to check it:

```bash
node scripts/build.js
```

It will tell you exactly which file has a problem, if any (missing name,
bad coordinates, unknown discipline, etc).

## Running locally

No install needed for the build step. To preview the site itself, serve the
folder with anything that can serve static files, e.g.:

```bash
node scripts/build.js
npx http-server . -p 8080
# open http://localhost:8080
```

(Opening `index.html` directly via `file://` won't work — `fetch()` needs an
actual HTTP server.)

## Deploying to GitHub Pages

1. Push this repo to GitHub.
2. In the repo settings, go to **Settings → Pages** and set **Source** to
   **GitHub Actions**.
3. Push to `main` (or run the workflow manually from the **Actions** tab).
   The included workflow (`.github/workflows/deploy.yml`) rebuilds
   `data/gyms.json` from your markdown files and deploys automatically —
   you never need to commit the generated JSON yourself, though it's fine
   if it's in the repo too.
4. Your site will be live at `https://<your-username>.github.io/<repo-name>/`.

## Customizing

- **Map area** — `MAP_CENTER`, `MAP_ZOOM`, and `MAP_BOUNDS` near the top of
  `js/map.js` control the initial view and the max-pan bounds.
- **Colors / fonts** — all in the `:root` block at the top of `css/style.css`.
- **The dashed trail line** connects visited gyms in order of `lastVisit` —
  drop that field from a gym's frontmatter to leave it out of the trail.

## Seed data

The `gyms/` folder ships with six real gyms to show the format working end
to end — a couple in Amsterdam, one in Eindhoven, two in Belgium (Hasselt,
Antwerp), and one in Aachen, Germany. Coordinates are approximate — nudge
them if you spot a gym in the wrong spot, then delete or replace these
entries with your own logbook. Two (`the-island-antwerp`, `diehalle-aachen`)
are marked `checked: true` since their address came straight from the gym's
own site; the rest are `checked: false` so you can see the "Verified only"
filter actually filtering something — re-verify all of them before trusting
the pins.
