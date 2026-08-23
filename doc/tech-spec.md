# Tech specification

**Purpose.** What the project is built with, and — more importantly — *why*, including what was
rejected and which risks were knowingly accepted.

**What belongs here.** Stack choices, architectural rules, testing strategy, platform/support
targets, and any decision that constrains how code gets written across the whole project.

**What doesn't.** Domain rules (domain-spec), per-feature behavior (implementation-spec), visual
tokens (style-guide), build sequencing (tracking), and how any of it runs on a particular machine
(environment).

**Rule of thumb.** A choice belongs here if violating it in one module would be a problem for the
project as a whole. Note *choice*: a description of what's true on your machine isn't one, which
is why it lives in [environment.md](environment.md) instead.

---

## Stack

- **Data:** one markdown file per gym in `gyms/*.md`, YAML-ish frontmatter + free-text body. This
  is the single source of truth — everything else is derived from it.
- **Build:** `scripts/build.js`, a hand-rolled Node script with **zero npm dependencies**. Compiles
  `gyms/*.md` → `data/gyms.json`.
- **Frontend:** static HTML/CSS/vanilla JS, no framework, no bundler, no transpile step.
  [Leaflet](https://leafletjs.com/) 1.9.4 (via unpkg CDN) renders the map; markers are custom
  inline SVG, not Leaflet's default pins.
- **Fonts:** Google Fonts (Space Grotesk, IBM Plex Sans, IBM Plex Mono), loaded via `<link>`.
- **Hosting:** GitHub Pages, deployed by `.github/workflows/deploy.yml` on every push to `main`.

## Architecture

- **`gyms/*.md` is the only thing a person edits.** `data/gyms.json` is a generated artifact —
  committed for convenience (so Pages doesn't need a build step at deploy time beyond what CI
  already runs), but nothing should hand-edit it. `scripts/build.js` is the only writer.
- **`js/map.js` only ever reads `data/gyms.json`** via `fetch`; it has no path back to
  `gyms/*.md` and doesn't need one.
- **Discipline colors are duplicated on purpose, and must be kept in sync by hand.** They're
  design tokens in `css/style.css`'s `:root` block, *and* literal hex strings in
  `DISCIPLINE_COLOR` / `UNVISITED_COLOR` / `OUTDOOR_WALL_COLOR` at the top of `js/map.js`. This
  isn't an oversight — the hold-shaped markers are inline SVG built as template strings, which
  can't read CSS custom properties. Changing a discipline's color in only one of the two places is
  a real, easy-to-make mistake with no build-time check to catch it — mitigated only by
  code-conventions.md's module-header-comment convention, not by anything automated.

## Tooling

- **Dev:** `npm run dev` — regenerates `data/gyms.json` then serves the folder statically on
  `http://localhost:8080` via `http-server`. `npm run gyms:generate` runs just the regenerate step
  (see [code-conventions.md](code-conventions.md)'s derived-asset convention).
- **Tests:** `npm test` — Node's built-in test runner (`node --test`), no test framework
  dependency. Covers `scripts/build.js`'s frontmatter parser and per-file validation.
- **E2E:** `npm run test:e2e` — Playwright, deliberately thin: one desktop-viewport and one
  mobile-viewport smoke pass, reserved for wiring the unit layer structurally can't see (real CSS
  media queries, real click/tap behavior). Requires Node ≥20 (see environment.md).

---

## Decisions

### Hand-rolled frontmatter parser, no dependency

**Chosen:** a small hand-rolled parser in `scripts/build.js` (flat `key: value` lines, quoted or
bare strings, numbers, booleans, `[...]` string arrays).

**Why:** the frontmatter format this project actually needs is intentionally simple, and never
needs nested objects, multi-line strings, or YAML's other corners. Zero dependencies means
`node scripts/build.js` (or CI's identical step) runs forever without an `npm install`, on any
machine with a Node binary and nothing else.

**Rejected:** `gray-matter`. It was listed in `package.json`'s `dependencies` but never actually
imported anywhere — dead weight left over from an earlier pass, contradicting the "no npm
dependencies required" claim the README makes elsewhere. Removed.

**Accepted risk:** the parser does no type coercion beyond what `loadGym` explicitly checks
(`name`, `lat`/`lon` as numbers, `discipline` against the allowed list). A typo like
`bucketList: yes` (rather than `true`) silently becomes the *string* `"yes"`, which every
`=== true` check in the codebase then treats as `false` — no error, no warning. Acceptable because
the frontmatter is hand-written by one person who wrote the parser; not acceptable if a second
contributor joins without also reading this file.

### Discipline colors live in two files

**Chosen:** duplicate the palette as literal values in `js/map.js`, alongside the CSS custom
properties in `css/style.css`.

**Why:** the hold-shaped map markers are inline SVG constructed as JS template strings — there's
no DOM element for them to inherit `var(--boulder)` etc. from at the point the string is built.

**Rejected:** computing the color at render time via `getComputedStyle(document.documentElement)`
and reading the CSS custom property. Would remove the duplication, but adds a DOM read on every
marker render and a runtime dependency on CSS having loaded first — more moving parts than this
project's marker count (currently under 100) justifies.

**Accepted risk:** the two lists drift if only one is edited. Currently mitigated only by a note
in the README and this doc — not by any automated check.

### Build-time duplicate-coordinate / duplicate-slug detection

**Chosen (Stage 2):** after `loadGym` compiles every file, `main()` runs a second pass over the
full in-memory list — not per-file, since a single file has nothing to collide with — grouping by
`(lat, lon)` and by `slug`. Any group with more than one member is a build error: `fail()` for
each offending file, naming the other file(s) it collides with, same as an existing per-file
validation error. `process.exitCode` ends up `1`, so `npm run gyms:generate` and CI both fail
loudly instead of silently emitting a `gyms.json` with a stacked/invisible pin.

**Why:** domain-spec.md §3 documents two real incidents where this exact mistake (a copy-pasted
file keeping the source's coordinates) shipped unnoticed until someone diffed the JSON by hand.
The check is pure, synchronous, and has no new dependency — same shape as the existing per-file
`validateGym`, just run once over the whole list instead of once per file.

**Rejected:** warning instead of failing the build. A duplicate coordinate is never intentional
(see domain-spec.md §1 — "a gym's identity is its coordinates, in practice") and always hides a
real venue, so there's no legitimate case to merely warn about.

**Test plan:** `test/build.test.js` gets two fixture gyms sharing coordinates (proving the
lat/lon check fires) and, separately, two sharing a slug (proving the slug check fires
independently) — mirroring how both real incidents were shaped differently (one a same-name
duplicate file, one a copy-paste that kept the source's coordinates but not its name).

---

## Testing strategy

- **`node --test` (fast layer) carries the bulk.** `scripts/build.js`'s parsing and validation
  logic is pure, synchronous, and has no DOM or network dependency — cheap to test directly, and
  the layer that should catch a frontmatter-format regression before it reaches CI.
- **Playwright (slow layer) is deliberately thin.** Two smoke passes — desktop and mobile viewport
  — covering: the map loads real data, a discipline filter chip changes what's shown, and the
  mobile collapsible-filters behavior (folded by default, active filters shown as badges, expands
  on tap) actually works in a real browser. Reserved for exactly the CSS-media-query and
  click/viewport wiring the unit layer structurally cannot see.
- Visual review (does a color read at the right contrast, does a layout actually look right) stays
  manual/ad hoc — screenshotted per change during review, not automated. See
  [style-guide.md](style-guide.md) for the tokens a screenshot is checked against.

---

## Future direction

Things deliberately out of scope now, where a decision is being made *today* to keep them
possible later.

- **No JSON schema / TypeScript for the frontmatter shape.** The hand-rolled parser (see
  Decisions) is accepted as "enough" for a single-author dataset; a schema would catch more, at
  the cost of the dependency-free build this project deliberately keeps.
- **No backend, no database, no multi-user anything.** This is a personal log for one person's own
  visits and bucket list — not a product with accounts. That's not a gap to fill later; it's the
  design.
