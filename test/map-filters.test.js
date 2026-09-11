// test/map-filters.test.js
// Mirrors js/map.js's passesFilters — tech.architecture's A-2 file-organization rule.
//
// domain.gym R-3/R-4/R-5/R-6/R-7's filter-combination logic, at the fast layer, now that
// passesFilters takes filter state explicitly instead of reading module globals (see js/map.js's
// import guard and passesFilters/currentFilters split). Previously only reachable through a full
// Playwright browser run; e2e/map.spec.js keeps thinner wiring-only coverage of the same chips —
// this file owns exhaustive correctness of the combination rules themselves.

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { passesFilters } from "../js/map.js";

const NO_FILTERS = { hasOutdoorWall: false, visitedOnly: false, bucketListOnly: false, activeDisciplines: new Set() };

function gym(overrides = {}) {
  return {
    slug: "test-gym",
    name: "Test Gym",
    discipline: ["boulder"],
    hasOutdoorWall: false,
    visited: true,
    bucketList: false,
    ...overrides,
  };
}

describe("passesFilters — no filters active", () => {
  test("passes every gym regardless of its data", () => {
    assert.equal(passesFilters(gym(), NO_FILTERS), true);
    assert.equal(passesFilters(gym({ visited: false, bucketList: true, hasOutdoorWall: true }), NO_FILTERS), true);
  });
});

describe("passesFilters — discipline (domain.gym R-4)", () => {
  test("passes a gym with any active discipline", () => {
    const filters = { ...NO_FILTERS, activeDisciplines: new Set(["boulder"]) };
    assert.equal(passesFilters(gym({ discipline: ["boulder", "lead"] }), filters), true);
  });

  test("rejects a gym with none of the active disciplines", () => {
    const filters = { ...NO_FILTERS, activeDisciplines: new Set(["speed"]) };
    assert.equal(passesFilters(gym({ discipline: ["boulder"] }), filters), false);
  });
});

describe("passesFilters — has outdoor wall (domain.gym R-5)", () => {
  test("passes only gyms with hasOutdoorWall: true", () => {
    const filters = { ...NO_FILTERS, hasOutdoorWall: true };
    assert.equal(passesFilters(gym({ hasOutdoorWall: true }), filters), true);
    assert.equal(passesFilters(gym({ hasOutdoorWall: false }), filters), false);
  });
});

describe("passesFilters — visited only (domain.gym R-6)", () => {
  test("passes only visited gyms", () => {
    const filters = { ...NO_FILTERS, visitedOnly: true };
    assert.equal(passesFilters(gym({ visited: true }), filters), true);
    assert.equal(passesFilters(gym({ visited: false }), filters), false);
  });
});

describe("passesFilters — bucket list's narrower-than-the-field asymmetry (domain.gym R-7)", () => {
  // doc/spec/domain/gym.md's own worked example, reused here as literal data rather than fetched
  // from the live dataset — independent of whatever gyms/*.md happens to contain.
  const bjoeksExcalibur = gym({ name: "Bjoeks Excalibur", bucketList: true, visited: false });
  const alreadyVisitedBucketListGym = gym({ name: "Loved It, Went Back", bucketList: true, visited: true });
  const ordinaryVisitedGym = gym({ name: "Ordinary Gym", bucketList: false, visited: true });

  test("bucket list alone shows the unvisited bucket-list gym, not the visited one", () => {
    const filters = { ...NO_FILTERS, bucketListOnly: true };
    assert.equal(passesFilters(bjoeksExcalibur, filters), true);
    assert.equal(passesFilters(alreadyVisitedBucketListGym, filters), false);
    assert.equal(passesFilters(ordinaryVisitedGym, filters), false);
  });

  test("bucket list + visited together shows only the already-visited bucket-list gym", () => {
    const filters = { ...NO_FILTERS, bucketListOnly: true, visitedOnly: true };
    assert.equal(passesFilters(bjoeksExcalibur, filters), false);
    assert.equal(passesFilters(alreadyVisitedBucketListGym, filters), true);
    assert.equal(passesFilters(ordinaryVisitedGym, filters), false);
  });

  test("bucketList alone (no visited/bucketList-only filters active) is not narrowed at all", () => {
    // Confirms the asymmetry lives entirely in the filter combination, not in the data itself.
    assert.equal(passesFilters(bjoeksExcalibur, NO_FILTERS), true);
    assert.equal(passesFilters(alreadyVisitedBucketListGym, NO_FILTERS), true);
  });
});

describe("passesFilters — filter types combine with AND, not OR (domain.gym R-3)", () => {
  test("a gym must satisfy every active filter, not just one", () => {
    const filters = { ...NO_FILTERS, hasOutdoorWall: true, activeDisciplines: new Set(["boulder"]) };
    assert.equal(passesFilters(gym({ discipline: ["boulder"], hasOutdoorWall: true }), filters), true);
    // Matches the discipline but not hasOutdoorWall — OR would wrongly pass this.
    assert.equal(passesFilters(gym({ discipline: ["boulder"], hasOutdoorWall: false }), filters), false);
    // Matches hasOutdoorWall but not the discipline — OR would wrongly pass this too.
    assert.equal(passesFilters(gym({ discipline: ["lead"], hasOutdoorWall: true }), filters), false);
  });
});
