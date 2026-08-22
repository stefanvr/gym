# Climb Log

A personal map of climbing & bouldering gyms across the Netherlands, Belgium,
and the sliver of Germany around Limburg (Aachen) — like a "places I've
travelled" map, but for gyms and sessions.

Each gym is a markdown file with a bit of frontmatter. A small build script
compiles all of them into one JSON file that a [Leaflet](https://leafletjs.com/)
map reads. No database, no backend — just markdown, committed to git.

**[Live map →](https://stefanvr.github.io/gym/)**

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
discipline: ["boulder", "toprope"]   # any of: boulder, toprope, lead, speed
visited: true
bucketList: true    # this one's high on your want-to-go-next list
hasOutdoorWall: true                 # optional, adds it to the "Has outdoor wall" filter
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
  to yet; they still show on the map, greyed out, as a still-to-visit list.
- **`bucketList`** — set to `true` for the gyms you especially want to get
  to next; a personal priority marker, not a data-quality flag. You set it
  independently of `visited`, and bucket-list gyms get a small ✓ badge in
  the list and popup. The **"Bucket list" filter chip is deliberately
  narrower than the field**: on its own it shows the bucket-list gyms you
  *haven't* visited yet — the ones still to tick off. Combine it with
  "Visited only" to see the bucket-list gyms you've already done.
  Defaults to `false` if omitted.
- **`hasOutdoorWall`** — set to `true` for gyms with an outdoor wall; drives
  the "Has outdoor wall" filter chip. Defaults to `false` if omitted.
- Coordinates: right-click a spot on [Google Maps](https://maps.google.com)
  or [OpenStreetMap](https://www.openstreetmap.org) and copy the lat/lon.
- The **markdown body** becomes your notes — shown in the popup on the map.

Then rebuild locally to check it:

```bash
npm run build      # or: node scripts/build.js
```

It will tell you exactly which file has a problem, if any (missing name,
bad coordinates, unknown discipline, etc).

## Running locally

No install needed for the build step. To preview the site itself, serve the
folder with anything that can serve static files:

```bash
npm run dev        # build, then serve on http://localhost:8080
```

`npm run live` is also wired up, but it expects `live-server` to be
available (globally installed or via `npx`) — it isn't a project
dependency.

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
4. The site is live at <https://stefanvr.github.io/gym/>.

## Customizing

- **Map area** — `MAP_CENTER`, `MAP_ZOOM`, and `MAP_BOUNDS` near the top of
  `js/map.js` control the initial view and the max-pan bounds.
- **Colors / fonts** — design tokens live in the `:root` block at the top of
  `css/style.css`. Note that the discipline colours are also hard-coded in
  `DISCIPLINE_COLOR` / `UNVISITED_COLOR` / `OUTDOOR_WALL_COLOR` at the top of
  `js/map.js` (the markers are inline SVG, so they can't read CSS variables) —
  change a discipline colour in both places or the map and sidebar drift apart.
- **The dashed trail line** connects visited gyms in order of `lastVisit` —
  drop that field from a gym's frontmatter to leave it out of the trail.
