# Code conventions

**Purpose.** How code is written and organized, and — most importantly — how it stays connected to
the documents that specify it.

**What belongs here.** Conventions that apply across the codebase: file organization, what
comments are for, dev-only affordances.

**What doesn't.** Which technologies were chosen and why (tech-spec), what any particular feature
does (implementation-spec, domain-spec), and the process around changes (workflow).

---

## File organization

- `gyms/*.md` — the data. One file per gym (domain-spec.md §1).
- `scripts/build.js` — the only writer of `data/gyms.json`.
- `index.html` / `css/style.css` / `js/map.js` — the whole frontend. No further module split; the
  project is small enough that one file per layer (structure/style/behavior) is still the
  simplest thing that works.
- `data/gyms.json` — generated, committed anyway (tech-spec.md's Architecture section explains
  why). Never hand-edited.
- `test/` mirrors what it tests directly (`test/build.test.js` for `scripts/build.js`) rather than
  a deeper tree — there's currently one non-trivial module to test.
- `e2e/` holds Playwright specs, separate from `test/` per Playwright's own convention (and
  tech-spec.md's fast/slow layer split).

## Every module says what it implements

Open `scripts/build.js` and `js/map.js` with a comment naming the doc section each one
implements:

```js
// Compiles gyms/*.md -> data/gyms.json. Tech-spec.md's "Architecture" — the only writer of that
// file, and the frontend (js/map.js) never reads gyms/*.md directly.
```

```js
// Renders data/gyms.json as a Leaflet map + sidebar. Behavior specified in
// implementation-spec.md §1-7; discipline colors are tech-spec.md's "Discipline colors live in
// two files" decision — keep DISCIPLINE_COLOR/UNVISITED_COLOR/OUTDOOR_WALL_COLOR byte-identical
// to css/style.css's :root tokens.
```

Reading code, this is where you find the rule it's meant to satisfy. Changing a rule, it's where
you find what depends on it. Without it, the docs drift from the code silently — which has
already happened once in this project's real history (a stale "no npm dependencies" README claim
next to a `gray-matter` dependency nothing imported; a filter-chip label that said "Verified only"
long after the underlying field became a bucket-list marker).

## Comments explain *why*, and especially "why not the obvious thing"

The diff shows what changed. A comment's job is the reasoning that isn't recoverable from reading
the code:

```js
// A one-shot wsl.exe invocation tears down its children when it exits — background this with the
// harness's own backgrounding, not `&` inside the call.
```

Earns a comment every time:

- **A non-obvious constraint** that makes the simple version wrong (the mobile filter fold's
  `data-expanded` attribute doing nothing above 760px isn't a bug — say so, or someone "cleans up"
  the dead-looking state).
- **A deliberate asymmetry** — the bucket-list filter chip checking `visited` too, when the field
  itself doesn't (domain-spec.md §3). Undocumented, this reads as a bug and gets simplified back.
- **A shared value's reason for existing in two places** — the discipline-color duplication.
  Invisible from either single call site.

## Tests mirror the source layout

`test/{name}.test.js` for `scripts/{name}.js`. A module with meaningful logic and no matching test
file should be conspicuous — currently that's nothing, since `js/map.js` is DOM-and-fetch-driven
UI code covered by the Playwright layer instead, not unit tests.

Name tests as the behavior claimed, not the function called — `rejects a gym with no discipline`
rather than `loadGym validation works`.

## Determinism

Not currently applicable — nothing in this codebase uses randomness. If that changes (a "surprise
me" gym picker, say), route it through a seeded generator rather than the language's global one,
so a bug report or a generated result can be reproduced exactly.

## Dev-only affordances

None exist yet. If one gets built — a fixture gym set to jump straight to an interesting map
state instead of scrolling to find one, a flag that widens `MAP_BOUNDS` for testing — gate it
(a URL flag, an env check) so it can't ship enabled by accident, and document it in the README's
"Dev-only surfaces" section as it's built. They're forgotten within a month otherwise.

## Scratch work leaves no trace

Throwaway verification scripts (a probe against `data/gyms.json`, a temporary copy of the site
with one variable flipped to check a CSS state) are encouraged — this project's own retrofit made
heavy use of exactly this to verify the mobile filter fold before it shipped. Delete them in the
same session. Write their output somewhere the dev server doesn't serve or watch, so a live-reload
doesn't reset the state mid-check.
