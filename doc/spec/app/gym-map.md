# App — Gym Map (`app.gym-map`)

What a user does with Climb Log, the surfaces that structure lives on, and how each interaction is
performed and resolved — depends on `domain.gym` for the rules referenced below. Anything about
domain rules (`domain.gym`), visual/audio values (`style.foundation`), or technology choices
(`tech.architecture`) is requested here but not decided here.

## Surfaces

- **Map** — the primary surface. One marker per gym passing the active filters (`domain.gym`
  R-3–R-7).
- **Sidebar** — persistent alongside the map on desktop; stacked above it on mobile. Contains the
  stats row, the filters, and the gym list.
- **Map popup** — opens on top of the map when a marker or list card is activated.
- **Mobile filter fold** — a structural mode of the filters area that exists only at narrow
  viewports (≤760px): collapsed by default behind a toggle header, expandable on demand. Above
  that width the filters area is always expanded and the fold has no structural effect.

## Interaction

### Map & markers

- Leaflet map, initial view fit to the configured map bounds (NL/BE/DE-Limburg), pan clamped to
  those bounds, zoom clamped to a fixed range.
- Markers are entirely rebuilt on every filter change, not incrementally diffed.
- Clicking a marker opens its popup and highlights the matching sidebar card — the two views stay
  in sync in this one direction (marker → card).

### Stats row

- One stat per discipline, counting occurrences across **currently-filtered** gyms, not the full
  dataset — a gym with two disciplines counts once per discipline. Recomputed on every filter
  change.

### Filters

- Discipline chips, "Has outdoor wall," "Visited only," and "Bucket list" — one row. Clicking a
  chip toggles its own active state, then re-renders stats, markers, and the list. See
  `domain.gym` R-3–R-7 for the combination rules, especially bucket-list's narrower-than-the-field
  behavior (R-7).
- **Mobile fold** (≤760px only; no-op above that breakpoint):
  - The filters area is collapsed by default on load.
  - A toggle header replaces the full row when collapsed, showing a label, an expand indicator,
    and a summary of whichever filters are currently active — empty if none are.
  - Tapping the toggle flips expanded/collapsed and re-renders the toggle; the active-filter
    summary disappears once expanded, and reappears (updated) the next time a filter changes
    while collapsed.

### Gym list

- Sidebar list of every gym passing the active filters, alphabetical by name.
- Each card: name + bucket-list badge, place, discipline pills; a distinct dimmed treatment if not
  visited.
- Clicking a card (or activating it via keyboard) flies the map to that gym (zooming in if
  currently zoomed out further than a fixed threshold), opens its popup, and marks the card active
  — the reverse direction of the marker→card sync above.
- Empty state when the filter combination matches nothing.

### Map popup

- Opened by clicking a marker, or by activating a list card.
- Content: name + bucket-list badge, place, discipline pills, notes (the gym's free-text body, if
  any), a meta line (visited status — "Visited," "Last visit {date}," or "Not visited yet" —
  followed by rating if set), and a website link if set.

### Chalk-line trail

- A dashed line connecting every **visited** gym that has a `lastVisit` (`domain.gym`), in
  `lastVisit` order — gyms without `lastVisit` are simply skipped, not treated as an error.
- Drawn once at load, not recomputed on filter changes — it always reflects the full visited
  history regardless of what's currently filtered/shown.

### Data loading & error state

*(application behavior only — no domain-rule counterpart)*

On load, the generated gym data is fetched. On failure (non-OK response, network error, or the
file missing because the build step was never run), the gym list shows a plain-text error
instructing the reader to run the generate step first; the map still renders (empty, no markers)
rather than failing to load at all.
