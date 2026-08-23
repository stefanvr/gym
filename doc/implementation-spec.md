# Climb Log — Implementation spec

**Purpose.** Companion to domain-spec: that document specifies the *rules*; this one specifies the
**interaction and application behavior** built around them — how each part is presented and
operated, plus the application-only modules (menus, chrome, save/load) that have no rule-level
counterpart.

**What belongs here.** Per-element behavior: what a control does, what a click resolves to, what
gets shown and hidden, what each mode's entry and exit are.

**What doesn't.** Domain rules (domain-spec), stack/architecture decisions (tech-spec), visual
values (style-guide), build order (tracking), and the reasoning behind a given line of code — that
belongs in a code comment, next to the code.

**Organization.** By element/module, mirroring domain-spec's structure where a section
corresponds directly to one of its sections.

---

## 1. Map & markers

- Leaflet map, dark CARTO tile layer, initial view fit to `MAP_BOUNDS` (NL/BE/DE-Limburg), pan
  clamped to those bounds, zoom clamped 6–18 (`MAP_CENTER`/`MAP_ZOOM`/`MAP_BOUNDS` in `js/map.js`).
- One marker per gym that passes the active filters (domain-spec §2) — markers are entirely
  rebuilt on every filter change (`renderMarkers`), not incrementally diffed.
- Marker visual: hold-shaped SVG, striped by active discipline colors if visited, solid
  `--unvisited` gray if not, dimmed opacity if not visited, outline color signals bucket-list
  status. See style-guide.md §5.
- Clicking a marker opens its popup and highlights the matching sidebar card
  (`setActiveCard`) — the two views stay in sync in this one direction (marker → card).

## 2. Stats row

- One stat per discipline (`boulder`/`toprope`/`lead`/`speed`), counting occurrences across
  **currently-filtered** gyms, not the full dataset — a gym with two disciplines counts once
  per discipline. Recomputed on every filter change.

## 3. Filters

- Discipline chips, "Has outdoor wall," "Visited only," and "Bucket list" — one row, built by
  `renderFilters()`. Clicking a chip toggles its own `data-active` attribute and the corresponding
  JS filter-state variable, then re-renders stats, markers, and the list. See domain-spec §2–3 for
  the filter combination rules, especially bucket-list's narrower-than-the-field behavior.
- **Mobile fold** (≤760px only; no-op above that breakpoint):
  - The filter row lives inside `#filters-section`, collapsed (`data-expanded="false"`) by
    default on load.
  - A toggle header (`#filters-toggle`) replaces the full row when collapsed, showing a "Filters"
    label, a chevron (rotates on expand), and a badge summary of whichever filters are currently
    active (`activeFilterBadgesHtml()`) — empty if none are.
  - Tapping the toggle flips `filtersExpanded` and re-renders the toggle
    (`renderFilterToggle()`); the badges disappear once expanded, and reappear (updated) the next
    time a filter changes while collapsed.
  - Above 760px the toggle is `display:none` and `.filters` always shows — the JS state still
    exists but has no visible effect at that width.

## 4. Gym list

- Sidebar list of every gym passing the active filters, alphabetical by name (`renderList`).
- Each card: name + bucket-list badge, place, discipline pills; dimmed treatment if not visited.
- Clicking a card (or Enter/Space when focused) calls `focusGym`: flies the map to that gym
  (zooming in if currently zoomed out further than 12), opens its popup, and marks the card active
  — the reverse direction of §1's marker→card sync.
- Empty state ("No gyms match these filters.") when the filter combination matches nothing.

## 5. Map popup

- Opened by clicking a marker, or by `focusGym` from the list.
- Content: name + bucket-list badge, place, discipline pills, notes (the gym's markdown body, if
  any), a meta line (visited status — "Visited," "Last visit {date}," or "Not visited yet" —
  followed by rating if set), and a website link if set.

## 6. Chalk-line trail

- A dashed polyline connecting every **visited** gym that has a `lastVisit`, in `lastVisit` order
  — gyms without `lastVisit` are simply skipped, not treated as an error.
- Drawn once at load (`renderTrail`), not recomputed on filter changes — it always reflects the
  full visited history regardless of what's currently filtered/shown.

## 7. Data loading & error state

*(no domain-spec counterpart — application behavior only)*

- On load, `fetch`es `data/gyms.json`. On failure (non-OK response, network error, or the file
  missing because `scripts/build.js` was never run), the gym list shows a plain-text error
  instructing the reader to run `npm run gyms:generate` first; the map still renders (empty, no
  markers) rather than failing to load at all.
