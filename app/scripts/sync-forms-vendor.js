#!/usr/bin/env node
// Copy the shared legal wording and logo into forms-api/vendor.
//
// The React app is the source of truth. The forms container only sees
// forms-api/, so those two files are vendored and must stay identical.
"use strict";

const fs = require("fs");
const path = require("path");

const APP = path.join(__dirname, "..");
const pairs = [
  [
    path.join(APP, "forms-web/src/forms/legal.json"),
    path.join(APP, "forms-api/vendor/legal.json"),
  ],
  [
    path.join(APP, "forms-web/src/assets/amk-logo.png"),
    path.join(APP, "forms-api/vendor/amk-logo.png"),
  ],
];

let stale = false;
for (const [src, dest] of pairs) {
  const left = fs.readFileSync(src);
  const right = fs.existsSync(dest) ? fs.readFileSync(dest) : null;
  if (right && left.equals(right)) continue;
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
  stale = true;
  console.log(`[sync-forms-vendor] updated ${path.relative(APP, dest)}`);
}

if (stale) {
  console.error(
    "[sync-forms-vendor] vendor files changed. Commit forms-api/vendor before deploying, or the Word export in the container will not match the page.",
  );
  process.exit(1);
}
