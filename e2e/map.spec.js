// e2e/map.spec.js
// doc/spec/app/gym-map.md's Map & markers / Filters sections. Runs on both configured projects
// (Desktop Chrome, Mobile Chrome — playwright.config.js) unless a test explicitly checks the
// viewport and skips.

import { test, expect } from "@playwright/test";

/** Reads the same compiled data the page fetches, independently of the UI, as an expected-value
 * oracle — so a filter-combination test proves the UI against real data rather than only against
 * itself (before/after counts within the page can't catch a filter that's simply wrong). */
async function fetchGyms(page) {
  const res = await page.request.get("/data/gyms.json");
  return res.json();
}

/** Mobile starts with the filter row folded (doc/spec/app/gym-map.md's mobile fold); expand it so
 * chips are clickable, matching what a real visitor on that viewport would have to do first. */
async function expandFiltersIfFolded(page) {
  const toggle = page.locator("#filters-toggle");
  if (await toggle.isVisible()) {
    await toggle.click();
  }
}

test("the map loads real gym data", async ({ page }) => {
  await page.goto("/");

  // At least one discipline stat should be non-zero once data/gyms.json actually loads —
  // proof this isn't just the empty shell doc/spec/app/gym-map.md's "Data loading & error
  // state" describes on failure.
  const firstStatCount = page.locator(".stat__count").first();
  await expect(firstStatCount).toBeVisible();
  const count = Number(await firstStatCount.textContent());
  expect(count).toBeGreaterThan(0);

  await expect(page.locator(".gym-card").first()).toBeVisible();
});

test("a discipline filter chip narrows the gym list", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".gym-card").first()).toBeVisible();

  await expandFiltersIfFolded(page);

  const before = await page.locator(".gym-card").count();

  const boulderChip = page.locator('.filter-chip[data-value="boulder"]');
  await boulderChip.click();

  const after = await page.locator(".gym-card").count();
  expect(after).toBeLessThan(before);
  expect(after).toBeGreaterThan(0);

  // Toggling back off restores the original count — the filter isn't a one-way ratchet.
  await boulderChip.click();
  await expect(page.locator(".gym-card")).toHaveCount(before);
});

test("'Has outdoor wall' filter narrows to exactly the gyms that have one (domain.gym R-5)", async ({ page }) => {
  await page.goto("/");
  await expandFiltersIfFolded(page);

  const gyms = await fetchGyms(page);
  const expected = gyms.filter((g) => g.hasOutdoorWall).length;
  expect(expected).toBeGreaterThan(0); // otherwise this test would trivially pass on real data drift

  await page.locator('.filter-chip[data-kind="hasOutdoorWall"]').click();
  await expect(page.locator(".gym-card")).toHaveCount(expected);
});

test("'Visited only' filter narrows to exactly the visited gyms (domain.gym R-6)", async ({ page }) => {
  await page.goto("/");
  await expandFiltersIfFolded(page);

  const gyms = await fetchGyms(page);
  const expected = gyms.filter((g) => g.visited).length;
  expect(expected).toBeGreaterThan(0);

  await page.locator('.filter-chip[data-kind="visited"]').click();
  await expect(page.locator(".gym-card")).toHaveCount(expected);
});

test("filter types combine with AND, not OR, across chips (domain.gym R-3)", async ({ page }) => {
  await page.goto("/");
  await expandFiltersIfFolded(page);

  const gyms = await fetchGyms(page);
  const expected = gyms.filter((g) => g.discipline.includes("boulder") && g.hasOutdoorWall).length;
  expect(expected).toBeGreaterThan(0);
  expect(expected).toBeLessThan(gyms.filter((g) => g.discipline.includes("boulder")).length);

  await page.locator('.filter-chip[data-value="boulder"]').click();
  await page.locator('.filter-chip[data-kind="hasOutdoorWall"]').click();
  await expect(page.locator(".gym-card")).toHaveCount(expected);
});

test.describe("bucket list filter's narrower-than-the-field asymmetry (domain.gym R-7)", () => {
  // doc/spec/domain/gym.md's own worked example: Bjoeks Excalibur is bucketList:true,
  // visited:false — the exact case the rule's asymmetry is about. Named directly rather than only
  // via counts, so a regression that swaps R-7's AND for an OR is caught even if it happened to
  // preserve the overall count.
  const WORKED_EXAMPLE = "Bjoeks Excalibur";

  test("bucket list alone shows an unvisited bucket-list gym", async ({ page }) => {
    await page.goto("/");
    await expandFiltersIfFolded(page);

    const gyms = await fetchGyms(page);
    const expected = gyms.filter((g) => g.bucketList && !g.visited).length;
    expect(expected).toBeGreaterThan(0);
    expect(gyms.some((g) => g.name === WORKED_EXAMPLE && g.bucketList && !g.visited)).toBe(true);

    await page.locator('.filter-chip[data-kind="bucketList"]').click();
    await expect(page.locator(".gym-card")).toHaveCount(expected);
    await expect(page.locator(".gym-card", { hasText: WORKED_EXAMPLE })).toBeVisible();
  });

  test("bucket list + visited together hides it, showing only already-visited bucket-list gyms", async ({ page }) => {
    await page.goto("/");
    await expandFiltersIfFolded(page);

    const gyms = await fetchGyms(page);
    const expected = gyms.filter((g) => g.bucketList && g.visited).length;
    expect(expected).toBeGreaterThan(0);

    await page.locator('.filter-chip[data-kind="bucketList"]').click();
    await page.locator('.filter-chip[data-kind="visited"]').click();
    await expect(page.locator(".gym-card")).toHaveCount(expected);
    await expect(page.locator(".gym-card", { hasText: WORKED_EXAMPLE })).toHaveCount(0);
  });
});

test.describe("mobile collapsible filters (doc/spec/app/gym-map.md's mobile fold)", () => {
  test("folded by default below the 760px breakpoint, full row shown above it", async ({ page }) => {
    await page.goto("/");
    const viewportWidth = page.viewportSize().width;
    const isMobileViewport = viewportWidth <= 760;

    const filtersRow = page.locator("#filters");
    const toggle = page.locator("#filters-toggle");

    if (isMobileViewport) {
      await expect(toggle).toBeVisible();
      await expect(filtersRow).toBeHidden();

      await toggle.click();
      await expect(filtersRow).toBeVisible();
    } else {
      await expect(toggle).toBeHidden();
      await expect(filtersRow).toBeVisible();
    }
  });

  test("an active filter shows as a badge while folded", async ({ page }) => {
    await page.goto("/");
    const viewportWidth = page.viewportSize().width;
    test.skip(viewportWidth > 760, "folding only applies below the 760px breakpoint");

    // Expand, activate a filter, then collapse again — the badge should summarize it.
    await page.locator("#filters-toggle").click();
    await page.locator('.filter-chip[data-kind="hasOutdoorWall"]').click();
    await page.locator("#filters-toggle").click();

    await expect(page.locator("#filters-toggle-badges")).toContainText("Outdoor wall");
  });
});
