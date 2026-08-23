# Climb Log — Domain Specification

**Purpose.** What this thing *is* and what its rules are, independent of how it's built.

**What belongs here.** The problem domain: entities, their properties, the rules governing them,
and the edge cases those rules produce. Written so someone could reason about the product — or
play the game, or work the process — without reading a line of code.

**What doesn't.** Anything technical (tech-spec), anything about how it's presented or operated
(implementation-spec), anything visual (style-guide), and anything about build order (tracking).

**Rule of thumb.** If changing it would change *what the product does*, it belongs here. If
changing it would only change *how the product is made*, it doesn't.

---

## 1. Gyms

A **gym** is one climbing or bouldering venue — one building, one location. A chain with several
locations (e.g. Neoliet, Beest Boulders) gets one gym entry per location, not one per chain.

| Field | Type | Required | Default if omitted | Notes |
|---|---|---|---|---|
| `name` | string | **yes** | — | The venue's own name. |
| `city` | string | no | `""` | |
| `country` | string | no | `""` | Informal ISO-2-ish (`NL`, `BE`, `DE`) — not validated. |
| `lat`, `lon` | number | **yes** | — | Decimal degrees. |
| `discipline` | list | **yes**, non-empty | — | One or more of `boulder`, `toprope`, `lead`, `speed`. |
| `visited` | boolean | no | **`true`** | See the callout below — this default is the opposite of what it looks like. |
| `bucketList` | boolean | no | `false` | A personal priority marker: "I especially want to get to this one next." Independent of `visited` — see §3. |
| `hasOutdoorWall` | boolean | no | `false` | |
| `rating` | number 1–5 | no | — | |
| `website` | URL string | no | — | |
| `lastVisit` | date string (`YYYY-MM-DD`) | no | — | Drives trail-line ordering; a visited gym with no `lastVisit` just isn't part of the trail. |
| body text | free text | no | `""` | Personal notes — vibe, route setting, who you went with. |

**Scope:** the Netherlands, Belgium, and the sliver of Germany around Limburg (Aachen) — a
day-trip radius from home, not a rule enforced anywhere in code.

**`visited` defaults to `true` if the field is omitted entirely** — the opposite of the intuitive
"absent means false." This matches how a gym normally gets logged (you went, so you add a file —
typing `visited: true` every time would be pure noise), but it's a real footgun for anything that
bulk-adds gyms you *haven't* been to: every not-yet-visited entry must explicitly write
`visited: false`, or it silently reads as visited. This has bitten a real bulk import in this
project's history and is worth remembering before writing a script that generates gym files.

**A gym's identity is its coordinates, in practice**, even though nothing enforces that they're
unique. Two gyms sharing a `(lat, lon)` pair render as one pin stacked on top of the other on the
map — effectively one of them becomes invisible. This has happened twice in this project's real
history (see §3) and both times was a copy-paste mistake, not a deliberate choice.

---

## 2. Filters

The sidebar's filter chips narrow which gyms show on the map and in the list. Filters combine with
**AND**: a gym must pass every active filter to show.

- **Discipline chips** (Boulder / Toprope / Lead / Speed) — a gym passes if it has *any* of the
  active disciplines, and if no discipline chip is active, all gyms pass this filter.
- **Has outdoor wall** — passes gyms with `hasOutdoorWall: true`.
- **Visited only** — passes gyms with `visited: true`.
- **Bucket list** — see §3; this one is deliberately not a plain `bucketList === true` check.

---

## 3. Interactions & edge cases

### The "Bucket list" filter is narrower than the `bucketList` field

`bucketList` is set independently of `visited` in the data — a gym can be both bucket-listed
*and* already visited (you loved it, you want to go back). But the **filter chip** answers a
different question than "which gyms have `bucketList: true`": on its own, it shows only the
bucket-list gyms **not yet visited** — the ones still to actually tick off.

- **Bucket list alone** → `bucketList === true AND visited === false`.
- **Bucket list + Visited only together** → `bucketList === true AND visited === true` — the
  bucket-list gyms you've *already* done.

*Worked example:* Bjoeks Excalibur is `bucketList: true, visited: false`. Tapping "Bucket list"
alone shows it. Also tapping "Visited only" hides it (it's not visited) and would instead show any
gym that's both bucket-listed and already visited, if one existed.

This is intentional, not a bug to "simplify" back to a plain field check — the whole point of the
chip is "what's next," and a bucket-list gym you've already been to isn't next.

### Two gyms can end up with identical coordinates

Nothing in the data model prevents two different gym files from carrying the same `(lat, lon)` —
the build step catches it (see tech-spec.md's "Build-time duplicate-coordinate / duplicate-slug
detection"), but nothing stops someone from writing the collision in the first place. It has
happened twice for two different reasons, both worth knowing before adding gyms in bulk:

- **A literal duplicate file.** Two files for the same gym, same coordinates, differing only in
  filename (a stray capital letter in one). Caught by manually diffing the built JSON for
  coordinate collisions, not by the build script.
- **A copy-pasted-and-half-edited file.** A new gym file created by copying a nearby one (same
  street, different building) and updating the name but not the coordinates. *Worked example:*
  Arnhem has two separate Climbing Network venues on the same street, ~250 m apart — Olympus 27
  (rope climbing) and Olympus 3 / RijnBoulder (bouldering). A file for the Olympus venue was
  created by copying the Rijnhal/RijnBoulder file, and kept Rijnhal's name *and* its exact
  coordinates. The mistake was only found by noticing two different gym slugs resolved to the
  identical lat/lon pair.

The rule this leaves standing: **every gym's coordinates should be unique**, enforced by the build
step failing loudly rather than assumed to be "obviously fine" or checked by hand.

---

## 4. Open questions

- **Should `visited` default to `false` instead of `true`?** Currently omitting it means
  "visited." The safer default for bulk-importing gyms you haven't been to would be the opposite —
  but that would make every gym logged the normal way (you went, so you're adding it) need an
  explicit `visited: true`, which is the far more common case. Not settled; noting the tension
  rather than picking a side is deliberate, since real history shows this default has cost time
  in the *less* common direction (a bulk backlog import once), not the common one.
