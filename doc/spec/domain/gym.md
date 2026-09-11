# Domain — Gym (`domain.gym`)

What this thing *is* and what its rules are, independent of how it's built: the problem domain —
entities, their properties, the rules governing them, and the edge cases those rules produce.
Written so someone could reason about the product without reading a line of code.

Anything visual, interactive, technical, or about build order belongs to `app.gym-map`,
`style.foundation`, or `tech.architecture` instead. If changing something would change *what the
product does*, it belongs here; if it would only change *how the product is made*, it doesn't.

## Concepts

A **gym** is one climbing or bouldering venue — one building, one location. A chain with several
locations (e.g. Neoliet, Beest Boulders) gets one gym entry per location, not one per chain.

**Scope:** the Netherlands, Belgium, and the sliver of Germany around Limburg (Aachen) — a
day-trip radius from home, not a rule enforced anywhere in code.

## Data

| Field | Type | Required | Default if omitted | Notes |
|---|---|---|---|---|
| `name` | string | **yes** | — | The venue's own name. |
| `city` | string | no | `""` | |
| `country` | string | no | `""` | Informal ISO-2-ish (`NL`, `BE`, `DE`) — not validated. |
| `lat`, `lon` | number | **yes** | — | Decimal degrees. |
| `discipline` | list | **yes**, non-empty | — | One or more of `boulder`, `toprope`, `lead`, `speed`. |
| `visited` | boolean | no | **`true`** | See R-1. |
| `bucketList` | boolean | no | `false` | A personal priority marker: "I especially want to get to this one next." Independent of `visited` — see R-7. |
| `hasOutdoorWall` | boolean | no | `false` | |
| `rating` | number 1–5 | no | — | |
| `website` | URL string | no | — | |
| `lastVisit` | date string (`YYYY-MM-DD`) | no | — | Drives trail-line ordering; a visited gym with no `lastVisit` just isn't part of the trail. |
| body text | free text | no | `""` | Personal notes — vibe, route setting, who you went with. |

## Rules

### R-1 — `visited` defaults to `true` when omitted

The opposite of the intuitive "absent means false." This matches how a gym normally gets logged
(you went, so you add a file — typing `visited: true` every time would be pure noise), but it's a
real footgun for anything that bulk-adds gyms you *haven't* been to: every not-yet-visited entry
must explicitly write `visited: false`, or it silently reads as visited. This has bitten a real
bulk import in this project's history and is worth remembering before writing a script that
generates gym files.

### R-2 — Every gym's coordinates must be unique

A gym's identity is its coordinates, in practice, even though nothing in the data model enforces
that they're unique. Two gyms sharing a `(lat, lon)` pair render as one pin stacked on top of the
other on the map — effectively one becomes invisible.

This has happened twice in this project's real history, both times a copy-paste mistake rather
than a deliberate choice: a literal duplicate file (same coordinates, differing only by a stray
capital letter in the filename), and a copy-pasted-and-half-edited file (a new gym file created by
copying a nearby one and updating the name but not the coordinates — Arnhem's Olympus 27 and
Olympus 3/RijnBoulder venues, ~250m apart, once collided this way). Enforcement — the build step
failing loudly rather than the collision being assumed "obviously fine" — is `tech.architecture`'s
concern; this rule states only that the collision is never valid domain state.

### R-3 — Filters combine with AND

A gym must pass every active filter to show, both on the map and in the gym list.

### R-4 — Discipline filter passes any active discipline

A gym passes the discipline filter if it has *any* of the active discipline chips (Boulder /
Toprope / Lead / Speed). If no discipline chip is active, all gyms pass this filter.

### R-5 — "Has outdoor wall" filter

Passes gyms with `hasOutdoorWall: true`.

### R-6 — "Visited only" filter

Passes gyms with `visited: true`.

### R-7 — "Bucket list" filter is narrower than the `bucketList` field

`bucketList` is set independently of `visited` in the data — a gym can be both bucket-listed *and*
already visited (you loved it, you want to go back). But the filter chip answers a different
question than "which gyms have `bucketList: true`":

- **Bucket list alone** → `bucketList === true AND visited === false` — the ones still to actually
  tick off.
- **Bucket list + Visited only together** → `bucketList === true AND visited === true` — the
  bucket-list gyms you've *already* done.

*Worked example:* Bjoeks Excalibur is `bucketList: true, visited: false`. Tapping "Bucket list"
alone shows it. Also tapping "Visited only" hides it (it's not visited).

This is intentional, not a bug to "simplify" back to a plain field check — the whole point of the
chip is "what's next," and a bucket-list gym you've already been to isn't next.

## Open questions

- **Should `visited` default to `false` instead of `true`?** Currently omitting it means
  "visited" (R-1). The safer default for bulk-importing gyms you haven't been to would be the
  opposite — but that would make every gym logged the normal way (you went, so you're adding it)
  need an explicit `visited: true`, the far more common case. Not settled; real history shows this
  default has cost time in the *less* common direction (a bulk backlog import once), not the
  common one.
