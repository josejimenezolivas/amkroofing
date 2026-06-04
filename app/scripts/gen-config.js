#!/usr/bin/env node
// Build-time generator for scripts/config.js (gitignored).
// On Vercel, the GOOGLE_MAPS_API_KEY secret is injected at build time; this writes it
// into the client-side config so window.GOOGLE_MAPS_API_KEY is defined in the browser.
// Run from the app/ directory (Vercel Root Directory = app): `node scripts/gen-config.js`.
"use strict";

const fs = require("fs");
const path = require("path");

const OUT = path.join(__dirname, "config.js");
const key = (process.env.GOOGLE_MAPS_API_KEY || "").trim();
const tileProvider = (process.env.TILE_PROVIDER || "google").trim();

if (!key) {
  console.warn("[gen-config] WARNING: GOOGLE_MAPS_API_KEY is empty — live building detection will be disabled.");
}

const contents = `// AUTO-GENERATED at build time by scripts/gen-config.js — do not edit by hand.
window.GOOGLE_MAPS_API_KEY = ${JSON.stringify(key || "YOUR_GOOGLE_MAPS_API_KEY")};
window.TILE_PROVIDER = ${JSON.stringify(tileProvider)};
`;

fs.writeFileSync(OUT, contents);
console.log(`[gen-config] wrote ${OUT} (key ${key ? "present" : "MISSING"}, tiles="${tileProvider}")`);
