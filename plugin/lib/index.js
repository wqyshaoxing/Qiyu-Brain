/**
 * Qiyu-Brain plugin for DeepSeek Harness.
 *
 * Registers a skill provider that serves the skills bundled under ../skills/.
 * Deliberately dependency-free: the host profile cannot resolve the app's
 * private packages (@deepseek-ai/schemastery, yaml, dsh-skill), so this file
 * parses frontmatter itself and uses only node: builtins.
 *
 * Contract modelled on @deepseek-ai/dsh-skill-office: export name / inject /
 * apply, call ctx.skills.registerProvider() with a provider exposing list()
 * and get().
 */

import { readFileSync, readdirSync, statSync } from "node:fs";
import { join, sep } from "node:path";
import { fileURLToPath } from "node:url";

/** Cordis plugin identity. */
export const name = "qiyu-brain";

/** The skill registry must exist before apply runs. */
export const inject = ["skills"];

/** Rank used for bundled skills; lower wins when names collide. */
const RANK = 600;

/** Provider name registered on ctx.skills. */
const PROVIDER = "qiyu-brain";

/** Where a catalog entry came from. */
const SOURCE = "bundled";

/**
 * Parse the YAML subset our skills use: scalars and inline lists.
 * Returns { name, description, invocation, content }.
 */
function parseSkill(raw, path) {
  const match = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(raw);
  if (match === null) {
    throw new Error(`qiyu-brain: ${path} has no YAML frontmatter`);
  }
  const fields = {};
  for (const line of match[1].split(/\r?\n/)) {
    const trimmed = line.trim();
    if (trimmed === "" || trimmed.startsWith("#")) continue;
    const pair = /^([A-Za-z0-9_-]+):\s*(.*)$/u.exec(line);
    if (pair === null) continue;
    let value = pair[2].trim();
    if (value.startsWith("[") && value.endsWith("]")) {
      value = value
        .slice(1, -1)
        .split(",")
        .map((part) => part.trim().replace(/^["']|["']$/gu, ""))
        .filter((part) => part !== "");
    } else {
      value = value.replace(/^["']|["']$/gu, "");
    }
    fields[pair[1]] = value;
  }
  if (typeof fields.description !== "string" || fields.description === "") {
    throw new Error(`qiyu-brain: ${path} has no description`);
  }
  const flag = (value, fallback) => {
    if (value === undefined) return fallback;
    const text = String(value).toLowerCase();
    if (["true", "yes", "on", "1"].includes(text)) return true;
    if (["false", "no", "off", "0"].includes(text)) return false;
    return fallback;
  };
  return {
    name: typeof fields.name === "string" && fields.name !== "" ? fields.name : undefined,
    description: fields.description,
    invocation: {
      modelInvocable: !flag(fields["disable-model-invocation"], false),
      userInvocable: flag(fields["user-invocable"], true),
    },
    content: raw.slice(match[0].length).trim(),
  };
}

/** Build catalog candidates from <root>/<skill>/SKILL.md. */
function discover(root) {
  const candidates = [];
  for (const entry of readdirSync(root, { withFileTypes: true })) {
    if (!entry.isDirectory() || entry.name.startsWith(".") || entry.name === "node_modules") continue;
    const directory = join(root, entry.name);
    const locator = join(directory, "SKILL.md");
    let parsed;
    try {
      if (!statSync(locator).isFile()) continue;
      parsed = parseSkill(readFileSync(locator, "utf8"), locator);
    } catch (error) {
      console.warn(`[qiyu-brain] skipped ${entry.name}: ${error.message}`);
      continue;
    }
    candidates.push({
      name: parsed.name ?? entry.name,
      description: parsed.description,
      invocation: parsed.invocation,
      provider: PROVIDER,
      source: SOURCE,
      rank: RANK,
      resourceBase: { kind: "directory", path: directory.split(sep).join("/") },
      locator,
    });
  }
  return candidates.sort((a, b) => a.name.localeCompare(b.name));
}

/**
 * Register the provider. Never throws during load: a broken bundle must not
 * take the host down, so failures degrade to an empty catalog plus a warning.
 */
export function apply(ctx, config = {}) {
  const root = config.skillsDir ?? fileURLToPath(new URL("../skills/", import.meta.url));
  let candidates = [];
  try {
    candidates = discover(root);
  } catch (error) {
    console.warn(`[qiyu-brain] skill discovery failed at ${root}: ${error.message}`);
  }

  const provider = {
    name: PROVIDER,
    list: () => Promise.resolve(candidates),
    async get(candidate) {
      const { rank: _rank, locator, ...summary } = candidate;
      const raw = readFileSync(locator, "utf8");
      return { ...summary, content: parseSkill(raw, locator).content };
    },
  };

  ctx.skills.registerProvider(() => provider);
}
