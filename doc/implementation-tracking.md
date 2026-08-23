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
- [ ] `npm test` — `node --test` unit coverage for `scripts/build.js`'s parser/validation
- [ ] `npm run test:e2e` — Playwright, desktop + mobile smoke pass
- [ ] `package.json`: `build` → `gyms:generate`, add `test`/`test:e2e`
- [ ] README rewritten to the template's shape (short pointer + doc links + dev commands +
      dev-only surfaces), with the detailed frontmatter-schema content that used to live there
      moved into domain-spec.md/implementation-spec.md where it actually belongs
- [ ] Full audit pass: read every doc against the actual current code, fix anything that drifted
      while this stage was in progress

---

## Stage 2 — Polishing

*Deferred items land here as they're found. Not started as its own pass yet — items below were
found during Stage 0/1 and parked here rather than either fixed on the spot or silently dropped.*

- [ ] Spec
- [ ] Edge-case sweep against domain-spec
- [ ] UI/UX pass
- [ ] Audit the docs against the actual implementation, and document any remaining gaps

---

# Backlog — features to plan later

- [ ] **Build-time duplicate-coordinate / duplicate-slug detection** in `scripts/build.js` —
      scoped out in tech-spec.md's Future direction. Two real occurrences in this project's
      history (a case-only-duplicate file; a copy-pasted file that kept another gym's
      coordinates) were both caught by hand, not by the build.
- [ ] **Touch-target sizing pass** on filter chips/badges — flagged, not measured, in
      style-guide.md's Open items.
- [ ] **Silk Bouldergym (Ede)** was still listed "coming soon" as of the backlog sweep that added
      it — worth confirming it's actually open before trusting that entry.
- [ ] **Huneboulder (Assen)** was deliberately left out of the backlog sweep entirely — no address
      had been published yet for Drenthe's first boulder gym. Revisit once one exists.
- [ ] **Arnhem's Valkenhuizen outdoor wall** (Arnhem-Noord, a different sports complex from the
      Olympus/RijnBoulder venues already logged) came up while researching one of those entries
      but was never itself investigated as a possible gym entry.

---

## Notes on checking items off

See [workflow.md](workflow.md) for the full routine. In short: check items off with a note on what
actually happened, add `Ad hoc:` items for things found and fixed along the way, and move anything
deliberately skipped to the polish stage with its reasoning rather than dropping it.
