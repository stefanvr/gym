# Implementation tracking

**Purpose.** The build plan and its running record: what gets built, in what order, and what
actually happened.

**What belongs here.** Stages, their checklists, notes on how each item really went, and the
backlog of deferred work.

**What doesn't.** The process itself — that's [workflow.md](workflow.md), which every stage below
follows.

Cross-references: [domain-spec.md](domain-spec.md), [tech-spec.md](tech-spec.md),
[style-guide.md](style-guide.md), [implementation-spec.md](implementation-spec.md).

---

## Stage 0 — Pre-template baseline

*This project existed before this doc set did. Rather than fabricate a granular stage-by-stage
history after the fact for work that already shipped, this is one honest summary — the real
history is the git log, which workflow.md itself says records divergences better than a
retrofitted checklist ever could.*

By the time this doc set was retrofitted onto the project, it already had, live at
<https://stefanvr.github.io/gym/>:

- The core pipeline (`gyms/*.md` → `scripts/build.js` → `data/gyms.json` → Leaflet map + sidebar),
  deployed to GitHub Pages on every push to `main`.
- 91 logged gyms across NL/BE/DE-Limburg, sourced from personal visits and a backlog sweep of
  public gym directories (NKBV, Resole, and others).
- The full filter set (discipline, outdoor wall, visited, bucket list) and the chalk-line trail.
- The `bucketList` field (renamed from an originally-misdocumented `checked` field, mid-project,
  once its real semantics as a personal priority marker — not a verification flag — became clear).
- A collapsible mobile filter panel, replacing a full chip row that had been eating most of the
  40vh mobile sidebar.
- Zero automated tests. Verification had been manual: `node --check`, rebuilding
  `data/gyms.json` and eyeballing the count, and ad hoc headless-Chrome screenshots at both
  desktop and mobile viewports for anything touching layout.

**Try it:** open <https://stefanvr.github.io/gym/> — the map renders with pins, the sidebar lists
gyms, filters work, and on a phone-width viewport the filter row is collapsed behind a "Filters"
toggle.

---

## Stage 1 — Retrofit onto the dev-template doc set

*Formalizes decisions and conventions that had only existed in conversation/session memory —
which template-doc-set/workflow.md's own opening line is exactly about — and adds the testing
layer Stage 0 never had.*

**Try it:** `npm run gyms:generate && npm test && npm run test:e2e` all pass; the eight `doc/*.md`
files exist and each accurately describes the shipped code, not an aspiration.

- [x] Spec — this doc set itself
- [x] `.gitattributes` (`* text=auto eol=lf`) and `.nvmrc` (Node 20, matching CI)
- [x] `doc/environment.md`, `doc/tech-spec.md`, `doc/domain-spec.md`, `doc/style-guide.md`,
      `doc/implementation-spec.md`, `doc/workflow.md`, `doc/code-conventions.md`
- [x] Module header comments on `scripts/build.js` and `js/map.js`, per code-conventions.md's
      "every module says what it implements"
- [x] `npm test` — `node --test` unit coverage for `scripts/build.js`'s parser/validation.
      Required splitting `loadGym` into pure `validateGym`/`buildGymRecord` functions first so
      the logic was testable without filesystem fixtures for most cases; 28 tests, all passing.
- [x] `npm run test:e2e` — Playwright, desktop + mobile smoke pass. *Ad hoc:* Node 18 (WSL's
      system default) is below Playwright's `>=20` floor — installed Node 20 via `nvm`
      (doc/environment.md) rather than touching the system Node. Chromium installed without
      `--with-deps`, since `sudo` needs a password in this environment and the browser launched
      fine without the extra system packages that flag would have apt-installed.
- [x] `package.json`: `build` → `gyms:generate`, added `test`/`test:e2e` and `@playwright/test`
- [x] README rewritten to the template's shape (short pointer + doc links + dev commands +
      dev-only surfaces); the detailed frontmatter field reference moved to domain-spec.md §1
- [x] Full audit pass: grepped for stale references to renamed scripts/fields left over from
      *this* stage's own changes (`npm run build`, `gray-matter`, `checked` field, "Verified
      only" label) — none found beyond intentional historical mentions in this doc set itself.
      Note this does *not* claim the docs are permanently drift-free — see
      code-conventions.md's "every module says what it implements" for the ongoing mechanism
      that's supposed to prevent the next drift, not just this retrofit's one-time check.

---

## Stage 2 — Resolve open gym-backlog entries

*Three loose ends surfaced during Stage 1's retrofit but were parked in the Backlog below rather
than resolved inline. Two are gym-data questions that need real-world research; the third is the
build-safety gap that let both of this project's real duplicate-coordinate incidents through
unnoticed. Huneboulder (Assen) deliberately stays in the Backlog rather than being pulled in
here: unlike these three, there's nothing to act on yet since no address has been published for
it. Touch-target sizing also stays in the Backlog — left there on purpose, not an oversight.*

**Try it:** the two gym-data items below end this stage either resolved with a sourced answer (a
gym file added, updated, or removed, backed by what was checked) or explicitly re-deferred with a
named reason. The duplicate-detection item ends with `node scripts/build.js` actually failing
when pointed at two fixture gyms sharing coordinates — proven, not just claimed.

- [ ] Spec
- [ ] **Confirm whether Silk Bouldergym (Ede) has actually opened.** It was logged during the
      backlog sweep while still listed "coming soon." If open, verify/update its details
      (address, disciplines) against its own site; if not, decide whether to keep it logged as
      `visited: false` or pull the entry until it's real.
- [ ] **Investigate Arnhem's Valkenhuizen outdoor wall** (Arnhem-Noord — a different sports
      complex from the already-logged Olympus/RijnBoulder venues) as a possible gym entry:
      confirm it exists, whether it's public or club-only, and its address if so.
- [ ] **Build-time duplicate-coordinate / duplicate-slug detection** in `scripts/build.js` — a
      pass over the full compiled gym list (not per-file, like today's validation) that fails the
      build if two gyms share a `(lat, lon)` pair or a slug, naming both files. Add a unit test
      (`test/build.test.js`) with two fixture gyms at identical coordinates to prove it actually
      fires, mirroring how the two real incidents this would have caught were found by hand.

---

## Stage 3 — Polishing

*Deferred items land here as they're found. Not started as its own pass yet — items below were
found during Stage 0/1 and parked here rather than either fixed on the spot or silently dropped.*

- [ ] Spec
- [ ] Edge-case sweep against domain-spec
- [ ] UI/UX pass
- [ ] Audit the docs against the actual implementation, and document any remaining gaps

---

# Backlog — features to plan later

- [ ] **Touch-target sizing pass** on filter chips/badges — flagged, not measured, in
      style-guide.md's Open items.
- [ ] **Huneboulder (Assen)** was deliberately left out of the backlog sweep entirely — no address
      had been published yet for Drenthe's first boulder gym. Revisit once one exists.

---

## Notes on checking items off

See [workflow.md](workflow.md) for the full routine. In short: check items off with a note on what
actually happened, add `Ad hoc:` items for things found and fixed along the way, and move anything
deliberately skipped to the polish stage with its reasoning rather than dropping it.
