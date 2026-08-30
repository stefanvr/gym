// test/build.test.js
// Mirrors scripts/build.js — doc/code-conventions.md's "tests mirror the source layout".
//
// Covers the pure parsing/validation/normalization logic directly, per doc/tech-spec.md's
// testing strategy: this layer has no DOM or network dependency, so unit-testing it in isolation
// is cheap and is where a frontmatter-format regression should get caught.

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import {
  parseValue,
  parseFrontmatter,
  validateGym,
  buildGymRecord,
  findDuplicates,
  loadConfig,
  loadGym,
} from "../scripts/build.js";

describe("parseValue", () => {
  test("parses booleans", () => {
    assert.equal(parseValue("true"), true);
    assert.equal(parseValue("false"), false);
  });

  test("parses numbers, including negatives and decimals", () => {
    assert.equal(parseValue("52.058458971807575"), 52.058458971807575);
    assert.equal(parseValue("-4.5"), -4.5);
    assert.equal(parseValue("4"), 4);
  });

  test("strips surrounding quotes from strings", () => {
    assert.equal(parseValue('"Climbing Network Amsterdam"'), "Climbing Network Amsterdam");
    assert.equal(parseValue("'Single quoted'"), "Single quoted");
  });

  test("leaves an unquoted bare string as-is", () => {
    assert.equal(parseValue("Nieuwegein"), "Nieuwegein");
  });

  test("a colon inside the value (e.g. a URL) does not get re-split", () => {
    // parseValue only ever sees the substring after the frontmatter line's first colon —
    // this documents that a URL value survives intact once it reaches parseValue.
    assert.equal(parseValue('"https://www.climbingnetwork.nl/"'), "https://www.climbingnetwork.nl/");
  });

  test("parses a string array, trimming and unquoting each item", () => {
    assert.deepEqual(parseValue('["boulder", "toprope", "lead"]'), ["boulder", "toprope", "lead"]);
  });

  test("parses an empty array", () => {
    assert.deepEqual(parseValue("[]"), []);
  });

  test("empty value becomes an empty string", () => {
    assert.equal(parseValue(""), "");
  });

  test("a bare word that looks like neither boolean nor number nor array stays a string", () => {
    // Real footgun this documents: `bucketList: yes` is not a boolean — it parses as the
    // *string* "yes", which every `=== true` check downstream then reads as false. No parse
    // error, no warning. See doc/tech-spec.md's "Hand-rolled frontmatter parser" accepted risk.
    assert.equal(parseValue("yes"), "yes");
  });
});

describe("parseFrontmatter", () => {
  test("splits frontmatter block from body", () => {
    const raw = [
      "---",
      'name: "Test Gym"',
      "lat: 52.1",
      "lon: 5.1",
      'discipline: ["boulder"]',
      "---",
      "Some notes about the gym.",
    ].join("\n");

    const { data, content } = parseFrontmatter(raw);
    assert.equal(data.name, "Test Gym");
    assert.equal(data.lat, 52.1);
    assert.equal(data.lon, 5.1);
    assert.deepEqual(data.discipline, ["boulder"]);
    assert.equal(content, "Some notes about the gym.");
  });

  test("a gym file with no body has empty content, not undefined", () => {
    const raw = ['---', 'name: "Test"', "lat: 1", "lon: 1", "---", ""].join("\n");
    const { content } = parseFrontmatter(raw);
    assert.equal(content, "");
  });

  test("handles CRLF line endings the same as LF", () => {
    const raw = ['---', 'name: "Test"', "lat: 1", "lon: 1", "---", "note"].join("\r\n");
    const { data, content } = parseFrontmatter(raw);
    assert.equal(data.name, "Test");
    assert.equal(content, "note");
  });

  test("a comment line inside the frontmatter block is skipped", () => {
    const raw = [
      "---",
      "# this is a comment, not a field",
      'name: "Test"',
      "lat: 1",
      "lon: 1",
      "---",
      "",
    ].join("\n");
    const { data } = parseFrontmatter(raw);
    assert.equal(data.name, "Test");
    assert.equal("#" in data, false);
  });

  test("content with no frontmatter block at all returns empty data", () => {
    const { data, content } = parseFrontmatter("just some plain text, no --- delimiters");
    assert.deepEqual(data, {});
    assert.equal(content, "just some plain text, no --- delimiters");
  });
});

describe("validateGym", () => {
  const validData = { name: "Test", lat: 52.1, lon: 5.1, discipline: ["boulder"] };

  test("accepts a fully valid gym", () => {
    assert.deepEqual(validateGym(validData), []);
  });

  test("rejects a missing name", () => {
    const errors = validateGym({ ...validData, name: undefined });
    assert.ok(errors.some((e) => e.includes("name")));
  });

  test("rejects non-numeric lat/lon", () => {
    const errors = validateGym({ ...validData, lat: "not a number" });
    assert.ok(errors.some((e) => e.includes("lat")));
  });

  test("rejects an empty discipline list", () => {
    const errors = validateGym({ ...validData, discipline: [] });
    assert.ok(errors.some((e) => e.includes("discipline")));
  });

  test("rejects an unknown discipline", () => {
    const errors = validateGym({ ...validData, discipline: ["parkour"] });
    assert.ok(errors.some((e) => e.includes("parkour")));
  });

  test("accepts speed, the discipline once missing from the CSS token list", () => {
    // Not a parser edge case — a regression guard so "speed" specifically never silently drops
    // out of VALID_DISCIPLINES the way it briefly dropped out of css/style.css's :root block.
    assert.deepEqual(validateGym({ ...validData, discipline: ["speed"] }), []);
  });
});

describe("buildGymRecord", () => {
  const minimal = { name: "Test Gym", lat: 52.1, lon: 5.1, discipline: ["boulder"] };

  test("visited defaults to true when the field is entirely omitted", () => {
    // doc/domain-spec.md §1's explicitly-flagged surprising default.
    const gym = buildGymRecord("test-gym.md", minimal, "");
    assert.equal(gym.visited, true);
  });

  test("visited: false is honored", () => {
    const gym = buildGymRecord("test-gym.md", { ...minimal, visited: false }, "");
    assert.equal(gym.visited, false);
  });

  test("bucketList and hasOutdoorWall default to false when omitted", () => {
    const gym = buildGymRecord("test-gym.md", minimal, "");
    assert.equal(gym.bucketList, false);
    assert.equal(gym.hasOutdoorWall, false);
  });

  test("the slug is the filename without the .md extension", () => {
    const gym = buildGymRecord("nl-example-gym.md", minimal, "");
    assert.equal(gym.slug, "nl-example-gym");
  });

  test("the markdown body becomes notes verbatim", () => {
    const gym = buildGymRecord("test-gym.md", minimal, "Great route setting.");
    assert.equal(gym.notes, "Great route setting.");
  });

  test("optional fields default to null/empty rather than undefined", () => {
    const gym = buildGymRecord("test-gym.md", minimal, "");
    assert.equal(gym.website, null);
    assert.equal(gym.lastVisit, null);
    assert.equal(gym.rating, null);
    assert.equal(gym.city, "");
    assert.equal(gym.country, "");
  });
});

describe("findDuplicates", () => {
  test("no duplicates among gyms with distinct coordinates and slugs", () => {
    const gyms = [
      { slug: "a", lat: 52.1, lon: 5.1 },
      { slug: "b", lat: 52.2, lon: 5.2 },
    ];
    assert.deepEqual(findDuplicates(gyms), []);
  });

  test("flags two gyms sharing coordinates, naming both slugs", () => {
    // doc/domain-spec.md §3's "copy-pasted-and-half-edited file" incident: a new gym file kept
    // an existing one's exact lat/lon.
    const gyms = [
      { slug: "nl-olympus", lat: 51.98, lon: 5.9 },
      { slug: "nl-rijnboulder", lat: 51.98, lon: 5.9 },
    ];
    const dups = findDuplicates(gyms);
    assert.equal(dups.length, 1);
    assert.equal(dups[0].type, "coordinates");
    assert.deepEqual(dups[0].slugs, ["nl-olympus", "nl-rijnboulder"]);
  });

  test("flags two gyms sharing a slug, independently of coordinates", () => {
    const gyms = [
      { slug: "nl-example-gym", lat: 52.1, lon: 5.1 },
      { slug: "nl-example-gym", lat: 52.9, lon: 5.9 },
    ];
    const dups = findDuplicates(gyms);
    assert.equal(dups.length, 1);
    assert.equal(dups[0].type, "slug");
    assert.deepEqual(dups[0].slugs, ["nl-example-gym", "nl-example-gym"]);
  });

  test("an empty list has no duplicates", () => {
    assert.deepEqual(findDuplicates([]), []);
  });
});

describe("loadConfig (file I/O)", () => {
  test("no .gymrc falls back to the default gyms directory", () => {
    const missing = path.join(fs.mkdtempSync(path.join(os.tmpdir(), "climb-log-test-")), ".gymrc");
    assert.deepEqual(loadConfig(missing), { gymsDir: "gyms" });
  });

  test("reads a custom gymsDir from .gymrc", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "climb-log-test-"));
    try {
      const configFile = path.join(dir, ".gymrc");
      fs.writeFileSync(configFile, 'gymsDir: "my-gyms"\n');
      assert.deepEqual(loadConfig(configFile), { gymsDir: "my-gyms" });
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  test("a .gymrc present but missing gymsDir still falls back to the default", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "climb-log-test-"));
    try {
      const configFile = path.join(dir, ".gymrc");
      fs.writeFileSync(configFile, "# no gymsDir here\n");
      assert.deepEqual(loadConfig(configFile), { gymsDir: "gyms" });
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });
});

describe("loadGym (file I/O)", () => {
  test("reads a real file from a given directory and returns a compiled record", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "climb-log-test-"));
    try {
      fs.writeFileSync(
        path.join(dir, "test-gym.md"),
        ['---', 'name: "Test Gym"', "lat: 52.1", "lon: 5.1", 'discipline: ["boulder"]', "---", "notes"].join("\n")
      );
      const gym = loadGym("test-gym.md", dir);
      assert.equal(gym.name, "Test Gym");
      assert.equal(gym.slug, "test-gym");
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
    }
  });

  test("an invalid file returns null instead of throwing", () => {
    const dir = fs.mkdtempSync(path.join(os.tmpdir(), "climb-log-test-"));
    try {
      fs.writeFileSync(path.join(dir, "bad-gym.md"), ["---", "lat: 52.1", "lon: 5.1", "---", ""].join("\n"));
      assert.equal(loadGym("bad-gym.md", dir), null);
    } finally {
      fs.rmSync(dir, { recursive: true, force: true });
      // loadGym's failure path (fail()) sets process.exitCode = 1 as its CLI-reporting side
      // effect — deliberately exercised above, but it must not leak into node --test's own exit
      // code for an otherwise fully-passing run.
      process.exitCode = 0;
    }
  });
});
