// e2e/map.spec.js
// doc/implementation-spec.md §1-3. Runs on both configured projects (Desktop Chrome, Mobile
// Chrome — playwright.config.js) unless a test explicitly checks the viewport and skips.

import { test, expect } from "@playwright/test";

test("the map loads real gym data", async ({ page }) => {
  await page.goto("/");

  // At least one discipline stat should be non-zero once data/gyms.json actually loads —
  // proof this isn't just the empty shell doc/implementation-spec.md §7 describes on failure.
  const firstStatCount = page.locator(".stat__count").first();
  await expect(firstStatCount).toBeVisible();
  const count = Number(await firstStatCount.textContent());
  expect(count).toBeGreaterThan(0);

  await expect(page.locator(".gym-card").first()).toBeVisible();
});

test("a discipline filter chip narrows the gym list", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".gym-card").first()).toBeVisible();

  // On mobile the filter row starts folded (implementation-spec.md §3) — expand it first so the
  // chip is actually clickable, matching what a real visitor would have to do.
  const toggle = page.locator("#filters-toggle");
  if (await toggle.isVisible()) {
    await toggle.click();
  }

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

test.describe("mobile collapsible filters (doc/implementation-spec.md §3)", () => {
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
