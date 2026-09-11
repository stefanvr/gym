# Style — Foundation (`style.foundation`)

The visual vocabulary: tokens, components, and the states things can be shown in — concrete enough
that two people implementing different screens produce something that looks like one product.
Depends on `app.gym-map` for which surfaces/components exist; does not decide where a control
appears or what it does (that's `app.gym-map`), or rendering technology (`tech.architecture`).

## Tokens

Defined once, in `css/style.css`'s `:root` block — everything else in CSS references the token.

| Token | Value | Used for |
|---|---|---|
| `--basalt` | `#14171a` | App background |
| `--basalt-raised` | `#1d2226` | Panels (sidebar, popups) |
| `--basalt-line` | `#333a40` | Hairlines, borders |
| `--chalk` | `#edeae2` | Primary text on dark |
| `--chalk-dim` | `#9aa0a6` | Secondary text |
| `--boulder` | `#e8631c` | Discipline: boulder |
| `--toprope` | `#2f7de1` | Discipline: toprope |
| `--lead` | `#2e9e5b` | Discipline: lead |
| `--speed` | `#dd0d0d` | Discipline: speed |
| `--unvisited` | `#565c63` | Not-yet-visited gyms (markers, pills) |
| `--outdoor-wall` | `#bd197e` | "Has outdoor wall" filter/marker accent |
| `--radius` | `3px` | Corner radius, used everywhere something has one |

**These are mirrored as literal hex strings in `js/map.js`** (`DISCIPLINE_COLOR`,
`UNVISITED_COLOR`, `OUTDOOR_WALL_COLOR`) because the map markers are inline SVG and can't read CSS
custom properties. Changing a color here without changing it there is a real, easy mistake with no
build-time check — see `tech.architecture`'s "Discipline colors live in two files" decision. Keep
the two lists byte-identical.

## Typography

| Role | Font | Notes |
|---|---|---|
| Display | `Space Grotesk` (fallback: Helvetica Neue, Arial, sans-serif) | `h1`, popup gym names — titles only |
| Body | `IBM Plex Sans` (fallback: Helvetica Neue, Arial, sans-serif) | Everything else |
| Mono | `IBM Plex Mono` (fallback: ui-monospace, monospace) | Stats, filter chips, discipline pills, popup meta line — anything data-like or tabular in feel |

All three loaded from Google Fonts in `index.html`'s `<head>`.

## Layout & spacing

- **Desktop:** a two-column grid — 340px sidebar, `1fr` map — filling the viewport
  (`100vh`/`100dvh`).
- **Mobile (≤760px):** single column, sidebar stacked above the map, sidebar capped at `40vh` so
  the map is always at least partly visible without scrolling.
- **Touch targets:** not currently held to the ~44×44px accessibility floor. Filter chips and
  badges run 20–28px tall depending on padding, and the mobile filters-toggle header is ~44px tall
  including padding (close, not verified). See Open decisions.

## States & highlights

**Entity status** — "what is this thing?"

| State | Treatment |
|---|---|
| Visited | Full discipline color(s) on the marker/pills; normal text weight in the gym list. |
| Not visited | Marker and pills render in `--unvisited` gray instead of discipline colors; gym-card name dims to `--chalk-dim`; popup meta line reads "Not visited yet" instead of a last-visit date. |
| Bucket list | A small circular ✓ badge (background `--toprope`) next to the gym's name, in both the sidebar list and the map popup. Independent of the visited/not-visited treatment above — a gym can show both. |
| Has outdoor wall | No entity-level visual on the marker itself; surfaced only via the "Has outdoor wall" filter chip's dot color (`--outdoor-wall`). |

**Affordance overlays** — "what happens if I interact here?"

| Overlay | Treatment | Means |
|---|---|---|
| Filter chip active | Border and text switch from `--basalt-line`/`--chalk-dim` to `currentColor`/`--chalk` | This filter is currently applied |
| Filter chip hover | Text lightens to `--chalk` | Clickable |
| Focus (chip, filters-toggle) | 2px `--toprope` outline | Keyboard focus |
| Gym card hover / active | Faint white overlay (`rgba(255,255,255,0.04)`) + `--basalt-line` border | Hoverable / currently selected, synced to the open map popup |

Only one overlay class applies to a chip or card at a time in practice — there's no current case
of two competing on the same element, so no ranking rule exists yet.

## Components

| Component | Spec |
|---|---|
| **Hold-shaped marker** | Custom inline SVG (not a Leaflet default pin) — a rounded climbing-hold silhouette, striped horizontally into one band per active discipline color, with a thin outline: `#14171a` (basalt) if not bucket-listed, `#0e7c45` (green) if it is. Dimmed to 55% opacity when not visited. |
| **Discipline pill** | Small filled rounded-rect label — background is the discipline color (or `--unvisited` gray if the gym isn't visited), text is `--basalt`, mono font, uppercase, letter-spaced. |
| **Filter chip** | Bordered pill button, a colored dot + label, mono font. The bucket-list chip's "dot" is a ✓ glyph instead of a solid circle. |
| **Filter badge** | The mobile collapsed-filters summary. Visually lighter than a chip (no fill, smaller, non-interactive): a dot + label, or for bucket list specifically, green text/border instead of a dot. |
| **Filters-toggle** | Mobile-only header button — label, the badge row, and a chevron that rotates 180° when expanded. See `app.gym-map`'s mobile fold. |
| **Gym card** | Name + bucket-list badge, place, discipline pills. Hover/active states above. |
| **Map popup** | Leaflet's popup chrome restyled to the dark theme (`--basalt-raised` background, `--basalt-line` border); content is name + badge, place, pills, notes, a meta line (visited status · rating), and a website link. |
| **Chalk-line trail** | Dashed gray polyline (`#9aa0a6`, `2 7` dash) connecting visited gyms in `lastVisit` order — the one visual element with no discrete "component" styling, just a Leaflet polyline option set. |

## Open decisions

- **Touch-target sizing.** Filter chips/badges are smaller than the ~44×44px floor. Not measured
  precisely, not yet flagged as a real usability problem (this is a personal single-user tool) —
  worth a real pass if the mobile UI gets touched again, rather than assuming it's fine forever.
- **Ranking rule for overlapping affordance overlays.** None exists because no current UI state
  produces two at once. If one ever does, decide the ranking then rather than guessing
  preemptively.

## Reference implementation

The live site *is* the reference — <https://stefanvr.github.io/gym/>. There's no separate
component-preview page; the token/component set above is transcribed from, and should be checked
against, `css/style.css` directly.
