// scripts/build.js
// Reads every markdown file in /gyms, parses its YAML-ish frontmatter + body,
// and compiles the result into data/gyms.json for the map to fetch.
//
// doc/tech-spec.md's "Architecture" — this is the only writer of data/gyms.json;
// js/map.js never reads gyms/*.md directly. Per-file validation (doc/domain-spec.md §1) plus a
// whole-list duplicate-coordinate/slug check (doc/tech-spec.md's "Build-time duplicate-coordinate
// / duplicate-slug detection").
//
// No dependencies needed — the frontmatter format is intentionally simple
// (flat key: value pairs, string arrays, numbers, booleans, quoted strings)
// so a tiny hand-rolled parser is enough and there's nothing to `npm install`
// (doc/tech-spec.md's "Hand-rolled frontmatter parser, no dependency" decision).
//
// Run with: npm run gyms:generate  (or: node scripts/build.js)

import fs from "node:fs";
import path from "node:path";

const GYMS_DIR = path.resolve("gyms");
const OUT_FILE = path.resolve("data", "gyms.json");
const VALID_DISCIPLINES = ["boulder", "toprope", "lead", "speed"];

function fail(file, message) {
  console.error(`✖ ${file}: ${message}`);
  process.exitCode = 1;
}

/** Parses a single frontmatter scalar/array value into a JS value. */
function parseValue(raw) {
  const v = raw.trim();
  if (v === "") return "";
  if (v === "true") return true;
  if (v === "false") return false;
  if (/^-?\d+(\.\d+)?$/.test(v)) return parseFloat(v);
  if (v.startsWith("[") && v.endsWith("]")) {
    const inner = v.slice(1, -1).trim();
    if (inner === "") return [];
    return inner
      .split(",")
      .map((item) => item.trim().replace(/^["']|["']$/g, ""));
  }
  // Quoted or bare string
  return v.replace(/^["']|["']$/g, "");
}

/** Splits "---\nfrontmatter\n---\nbody" into { data, content }. */
function parseFrontmatter(raw) {
  const match = raw.match(/^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$/);
  if (!match) return { data: {}, content: raw.trim() };

  const [, fmBlock, body] = match;
  const data = {};
  for (const line of fmBlock.split(/\r?\n/)) {
    if (!line.trim() || line.trim().startsWith("#")) continue;
    const idx = line.indexOf(":");
    if (idx === -1) continue;
    const key = line.slice(0, idx).trim();
    const value = line.slice(idx + 1).trim();
    data[key] = parseValue(value);
  }
  return { data, content: body.trim() };
}

/**
 * Validates a parsed frontmatter object against doc/domain-spec.md §1's required fields.
 * Pure — no I/O — so it's unit-testable without touching the filesystem.
 * @returns {string[]} error messages; empty means valid.
 */
function validateGym(data) {
  const errors = [];

  if (!data.name) errors.push("missing `name`");
  if (typeof data.lat !== "number") errors.push("missing/invalid `lat` (must be a number)");
  if (typeof data.lon !== "number") errors.push("missing/invalid `lon` (must be a number)");

  const discipline = Array.isArray(data.discipline) ? data.discipline : [];
  const badDiscipline = discipline.filter((d) => !VALID_DISCIPLINES.includes(d));
  if (badDiscipline.length) {
    errors.push(`unknown discipline(s): ${badDiscipline.join(", ")} (allowed: ${VALID_DISCIPLINES.join(", ")})`);
  }
  if (discipline.length === 0) {
    errors.push("`discipline` is empty — add at least one of boulder / toprope / lead");
  }

  return errors;
}

/**
 * Turns already-parsed frontmatter + body into the normalized gym record the frontend consumes.
 * Pure — assumes `data` already passed validateGym. Field defaults are doc/domain-spec.md §1's
 * table; visited defaulting to true (not false) when omitted is deliberate, not a bug — see the
 * callout there.
 */
function buildGymRecord(file, data, content) {
  const discipline = Array.isArray(data.discipline) ? data.discipline : [];
  return {
    slug: file.replace(/\.md$/, ""),
    name: data.name,
    city: data.city || "",
    country: data.country || "",
    lat: data.lat,
    lon: data.lon,
    discipline, // e.g. ["boulder", "lead"]
    hasOutdoorWall: data.hasOutdoorWall === true, // default false
    visited: data.visited !== false, // default true — it's in the file, so you've probably been
    bucketList: data.bucketList === true, // default false — set true for gyms on your want-to-go-next list
    rating: typeof data.rating === "number" ? data.rating : null,
    website: data.website || null,
    lastVisit: data.lastVisit || null,
    notes: content,
  };
}

/**
 * Finds gyms in the compiled list that collide on coordinates or on slug — doc/domain-spec.md
 * §3's "every gym's coordinates should be unique" rule, checked across the whole list rather than
 * per-file (loadGym/validateGym only ever see one file at a time, so they can't catch this).
 * Pure — no I/O — so it's unit-testable without touching the filesystem.
 * @returns {{type: "coordinates"|"slug", key: string, slugs: string[]}[]} one entry per colliding group
 */
function findDuplicates(gyms) {
  const groupings = [
    { type: "coordinates", key: (g) => `${g.lat},${g.lon}` },
    { type: "slug", key: (g) => g.slug },
  ];

  return groupings.flatMap(({ type, key }) => {
    const bySlugs = new Map();
    for (const gym of gyms) {
      const k = key(gym);
      if (!bySlugs.has(k)) bySlugs.set(k, []);
      bySlugs.get(k).push(gym.slug);
    }
    return [...bySlugs.entries()]
      .filter(([, slugs]) => slugs.length > 1)
      .map(([key, slugs]) => ({ type, key, slugs }));
  });
}

/** Reads and compiles one gym file. The only function here that touches the filesystem. */
function loadGym(file, gymsDir = GYMS_DIR) {
  const raw = fs.readFileSync(path.join(gymsDir, file), "utf8");
  const { data, content } = parseFrontmatter(raw);
  const errors = validateGym(data);

  if (errors.length) {
    fail(file, errors.join("; "));
    return null;
  }

  return buildGymRecord(file, data, content);
}

function main() {
  if (!fs.existsSync(GYMS_DIR)) {
    console.error(`No gyms/ directory found at ${GYMS_DIR}`);
    process.exit(1);
  }

  const files = fs.readdirSync(GYMS_DIR).filter((f) => f.endsWith(".md"));
  const gyms = files.map((f) => loadGym(f)).filter(Boolean);

  for (const dup of findDuplicates(gyms)) {
    const what = dup.type === "coordinates" ? `coordinates (${dup.key})` : "slug";
    for (const slug of dup.slugs) {
      const others = dup.slugs.filter((s) => s !== slug).map((s) => `${s}.md`);
      fail(`${slug}.md`, `duplicate ${what} — also used by ${others.join(", ")}`);
    }
  }

  fs.mkdirSync(path.dirname(OUT_FILE), { recursive: true });
  fs.writeFileSync(OUT_FILE, JSON.stringify(gyms, null, 2));

  console.log(`✔ Compiled ${gyms.length}/${files.length} gym(s) → ${path.relative(process.cwd(), OUT_FILE)}`);
  if (process.exitCode === 1) {
    console.error("Build finished with errors — fix the file(s) above before deploying.");
  }
}

export {
  parseValue,
  parseFrontmatter,
  validateGym,
  buildGymRecord,
  findDuplicates,
  loadGym,
  VALID_DISCIPLINES,
};

// Only run the CLI build when invoked directly (`node scripts/build.js`), not when imported for
// tests — see test/build.test.js.
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
