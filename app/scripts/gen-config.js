#!/usr/bin/env node
// Build-time generator for scripts/config.js.
//
// This file used to write GOOGLE_MAPS_API_KEY into the client bundle, which shipped
// the key to every visitor. It no longer touches the key at all: Google calls go
// through the same-origin /api/* proxy, which reads GOOGLE_MAPS_API_KEY from the
// server environment. The only thing left here is a non-secret display flag.
//
// Run from the app/ directory (Vercel Root Directory = app): `node scripts/gen-config.js`.
"use strict";

const fs = require("fs");
const path = require("path");

const OUT = path.join(__dirname, "config.js");
const tileProvider = (process.env.TILE_PROVIDER || "google").trim().toLowerCase();

if (process.env.GOOGLE_MAPS_API_KEY) {
  console.log("[gen-config] GOOGLE_MAPS_API_KEY is set — used server-side by /api/* only, not written to the client.");
} else {
  console.warn("[gen-config] WARNING: GOOGLE_MAPS_API_KEY is not set — /api/solar, /api/geocode and /api/tiles will return 503.");
}

const contents = `// AUTO-GENERATED at build time by scripts/gen-config.js — do not edit by hand.
// Contains NO credentials. The Google API key lives only in the server environment.
window.TILE_PROVIDER = ${JSON.stringify(tileProvider)};
`;

fs.writeFileSync(OUT, contents);
console.log(`[gen-config] wrote ${OUT} (tiles="${tileProvider}", no secrets)`);
