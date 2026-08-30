# Climb Log

A personal map of climbing & bouldering gyms across the Netherlands, Belgium, and the sliver of
Germany around Limburg (Aachen) — like a "places I've travelled" map, but for gyms and sessions.

See [doc/domain-spec.md](doc/domain-spec.md) for what it does and the rules it follows,
[doc/tech-spec.md](doc/tech-spec.md) for technical decisions, and
[doc/implementation-tracking.md](doc/implementation-tracking.md) for the build plan.
New here? [doc/workflow.md](doc/workflow.md) is how work actually gets done.

**[Live map →](https://stefanvr.github.io/gym/)**

## Your own copy

Read the [getting started guide](getting-started.md) to have your own version.

## How it works

```
gyms/*.md  →  scripts/build.js  →  data/gyms.json  →  index.html + js/map.js
```

`gyms/*.md` is the only thing you hand-edit — see "Logging a gym" below and
[doc/domain-spec.md](doc/domain-spec.md) §1 for the full field reference. Everything else is
generated or static; [doc/tech-spec.md](doc/tech-spec.md)'s Architecture section has the details.

## Development

```bash
npm install
npm run dev          # regenerate data/gyms.json, then serve on http://localhost:8080
npm test              # unit tests (node --test) — scripts/build.js's parser/validation
npm run test:e2e      # Playwright smoke tests, desktop + mobile (needs Node >=20, see doc/environment.md)
npm run gyms:generate  # just the regenerate step
```

`npm run live` is also wired up, but expects `live-server` to be available globally or via
`npx` — it isn't a project dependency.

(Opening `index.html` directly via `file://` won't work — `fetch()` needs an actual HTTP server.)

## Dev-only surfaces

None currently. See [doc/code-conventions.md](doc/code-conventions.md)'s "Dev-only affordances"
for how one gets added and documented here if that changes.

## Logging a gym

Add a new file to `gyms/`, e.g. `gyms/base-camp-maastricht.md`:

```markdown
---
name: "Base Camp Maastricht"
city: "Maastricht"
country: "NL"
lat: 50.8514
lon: 5.6910
discipline: ["boulder", "toprope"]
visited: true
bucketList: false
website: "https://example.com"
lastVisit: "2026-08-01"
---
Whatever you want to remember: the vibe, the route setting, who you went
with, that one green boulder you finally sent.
```

Full field rules, defaults, and the two documented gotchas (`visited`'s default, and why
coordinates should be unique) live in [doc/domain-spec.md](doc/domain-spec.md) §1 — this is just
the shape. Coordinates: right-click a spot on [Google Maps](https://maps.google.com) or
[OpenStreetMap](https://www.openstreetmap.org) and copy the lat/lon.

Then rebuild locally to check it:

```bash
npm run gyms:generate
```

It will tell you exactly which file has a problem, if any (missing name, bad coordinates, unknown
discipline, etc).

## Deploying to GitHub Pages

Already set up for this repo — `.github/workflows/deploy.yml` rebuilds `data/gyms.json` and
deploys on every push to `main`, live at <https://stefanvr.github.io/gym/>. Setting this up on a
fork: Settings → Pages → Source → **GitHub Actions**, then push to `main` or run the workflow
manually from the Actions tab.

## Customizing

Design tokens are in [doc/style-guide.md](doc/style-guide.md) — but note discipline colors are
also hard-coded in `js/map.js` (inline-SVG markers can't read CSS variables); see
[doc/tech-spec.md](doc/tech-spec.md)'s "Discipline colors live in two files" decision before
changing one without the other. Map area (`MAP_CENTER`/`MAP_ZOOM`/`MAP_BOUNDS`) is near the top of
`js/map.js`. The dashed trail line connects visited gyms in `lastVisit` order — drop that field
from a gym's frontmatter to leave it out of the trail.
