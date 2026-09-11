# Tech — Architecture (`tech.architecture`)

What the project is built with, why, what was rejected, project-specific architecture rules that
constrain implementation, and which risks were knowingly accepted. A choice belongs here if
violating it in one module would be a problem for the project as a whole; a description of what's
true on one machine belongs to Setup Dev instead. Depends on `domain.gym` (the duplicate-coordinate
rule this scope's build check enforces) and `style.foundation` (the color tokens the duplication
decision below keeps in sync).

General code-structure/testing conventions that would remain useful on another project (seeded
randomness for reproducibility, gating dev-only affordances, spending comment effort on surprising
rather than obvious things) are the Software Design and General Guides' job, not repeated here —
see those Guides. This scope records only what's genuinely specific to Climb Log.

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

## Decisions

### Hand-rolled frontmatter parser, no dependency

**Chosen:** a small hand-rolled parser in `scripts/build.js` (flat `key: value` lines, quoted or
bare strings, numbers, booleans, `[...]` string arrays).

**Why:** the frontmatter format this project actually needs is intentionally simple, and never
needs nested objects, multi-line strings, or YAML's other corners. Zero dependencies means
`node scripts/build.js` (or CI's identical step) runs forever without an `npm install`, on any
machine with a Node binary and nothing else.

**Rejected:** `gray-matter`. It was listed in `package.json`'s `dependencies` but never actually
imported anywhere — dead weight left over from an earlier pass. Removed.

**Accepted risk:** the parser does no type coercion beyond what `loadGym` explicitly checks
(`name`, `lat`/`lon` as numbers, `discipline` against the allowed list). A typo like
`bucketList: yes` (rather than `true`) silently becomes the *string* `"yes"`, which every
`=== true` check in the codebase then treats as `false` — no error, no warning. Acceptable because
the frontmatter is hand-written by one person who wrote the parser; not acceptable if a second
contributor joins without also reading this scope.

### Discipline colors live in two files

**Chosen:** duplicate the palette as literal values in `js/map.js`, alongside the CSS custom
properties in `css/style.css` (`style.foundation`).

**Why:** the hold-shaped map markers are inline SVG constructed as JS template strings — there's
no DOM element for them to inherit `var(--boulder)` etc. from at the point the string is built.

**Rejected:** computing the color at render time via `getComputedStyle(document.documentElement)`
and reading the CSS custom property. Would remove the duplication, but adds a DOM read on every
marker render and a runtime dependency on CSS having loaded first — more moving parts than this
project's marker count (currently under 100) justifies.

**Accepted risk:** the two lists drift if only one is edited, with no automated check (A-4 states
the resulting constraint).

### Build-time duplicate-coordinate / duplicate-slug detection

**Chosen:** after `loadGym` compiles every file, `main()` runs a second pass over the full
in-memory list, grouping by `(lat, lon)` and by `slug`. Any group with more than one member is a
build error, naming every colliding file — the same `fail()` path as per-file validation.

**Why:** `domain.gym:R-2` — a duplicate coordinate is never valid domain state, and two real
incidents reached this project's history unnoticed until someone diffed the JSON by hand.

**Rejected:** warning instead of failing. There's no legitimate case to only warn about (A-5
states the resulting constraint).

## Architecture rules

### A-1 — One-way generated data flow

`gyms/*.md` is the only thing a person edits. `data/gyms.json` is a generated artifact — committed
for convenience (so Pages doesn't need a build step at deploy time beyond what CI already runs),
but nothing hand-edits it; `scripts/build.js` is its only writer. `js/map.js` only ever reads
`data/gyms.json` via `fetch`; it has no path back to `gyms/*.md` and doesn't need one.

### A-2 — File organization

- `gyms/*.md` — the data, one file per gym (`domain.gym`).
- `scripts/build.js` — the only writer of `data/gyms.json`.
- `index.html` / `css/style.css` / `js/map.js` — the whole frontend, one file per layer
  (structure/style/behavior). No further module split while the project stays this small.
- `test/` mirrors what it tests directly (`test/build.test.js` for `scripts/build.js`) rather than
  a deeper tree.
- `e2e/` holds Playwright specs, separate from `test/` per Playwright's own convention and this
  project's fast/slow test-layer split (see Testing strategy).

### A-3 — Every module says what it implements

`scripts/build.js` and `js/map.js` open with a comment naming the scope(s) each implements, e.g.:

```js
// Compiles gyms/*.md -> data/gyms.json. tech.architecture A-1 — the only writer of that file,
// and the frontend (js/map.js) never reads gyms/*.md directly.
```

Reading code, this is where you find the rule it's meant to satisfy. Changing a rule, it's where
you find what depends on it. Without it, the docs drift from the code silently — which has already
happened once in this project's real history (a stale "no npm dependencies" README claim next to a
`gray-matter` dependency nothing imported; a filter-chip label that said "Verified only" long after
the underlying field became a bucket-list marker).

### A-4 — Discipline colors must stay byte-identical across `js/map.js` and `css/style.css`

`DISCIPLINE_COLOR` / `UNVISITED_COLOR` / `OUTDOOR_WALL_COLOR` in `js/map.js` must match
`style.foundation`'s token values exactly. Changing one without the other is a real, easy mistake
with no build-time check to catch it.

### A-5 — Duplicate coordinates/slugs fail the build

After compiling every gym file, the build groups the full list by `(lat, lon)` and by slug; any
group with more than one member fails the build, naming every colliding file. Never downgraded to
a warning (`domain.gym:R-2`).

## Testing strategy

- **`node --test` (fast layer) carries the bulk.** `scripts/build.js`'s parsing and validation
  logic is pure, synchronous, and has no DOM or network dependency — the layer that should catch a
  frontmatter-format regression before it reaches CI.
- **Playwright (slow layer) is deliberately thin.** Two smoke passes — desktop and mobile viewport
  — covering: the map loads real data, a discipline filter chip changes what's shown, and the
  mobile collapsible-filters behavior actually works in a real browser. Reserved for exactly the
  CSS-media-query and click/viewport wiring the unit layer structurally cannot see. Requires
  Node ≥20 (see Setup Dev).
- Visual review (does a color read at the right contrast, does a layout actually look right) stays
  manual/ad hoc — screenshotted per change during review, not automated. See `style.foundation` for
  the tokens a screenshot is checked against.

## Future direction

Things deliberately out of scope now, where a decision is being made *today* to keep them possible
later — not gaps to fill, but the design:

- **No JSON schema / TypeScript for the frontmatter shape.** The hand-rolled parser is accepted as
  "enough" for a single-author dataset; a schema would catch more, at the cost of the
  dependency-free build this project deliberately keeps.
- **No backend, no database, no multi-user anything.** This is a personal log for one person's own
  visits and bucket list, not a product with accounts.
