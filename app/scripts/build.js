#!/usr/bin/env node
// Build the marketing site plus the forms app into dist/.
//
// Vercel Root Directory stays `app`. This script is the site service build.
// The forms API is a separate container service and is not built here.
"use strict";

const { execSync } = require("child_process");
const fs = require("fs");
const path = require("path");

const APP = path.join(__dirname, "..");
const DIST = path.join(APP, "dist");
const WEB = path.join(APP, "forms-web");

require("./gen-config.js");
require("./sync-forms-vendor.js");

if (!fs.existsSync(path.join(WEB, "node_modules"))) {
  execSync("npm ci", { cwd: WEB, stdio: "inherit" });
}
execSync("npm run build", { cwd: WEB, stdio: "inherit" });

fs.rmSync(DIST, { recursive: true, force: true });
copyTree(path.join(APP, "assets"), path.join(DIST, "assets"));
copyFile(path.join(APP, "index.html"), path.join(DIST, "index.html"));
copyFile(path.join(APP, "favicon.ico"), path.join(DIST, "favicon.ico"));
copyFile(path.join(APP, "site.webmanifest"), path.join(DIST, "site.webmanifest"));
copyFile(path.join(APP, "scripts", "config.js"), path.join(DIST, "scripts", "config.js"));
copyTree(path.join(WEB, "dist"), path.join(DIST, "forms"));

console.log(`[build] site + /forms -> ${DIST}`);

function copyFile(src, dest) {
  fs.mkdirSync(path.dirname(dest), { recursive: true });
  fs.copyFileSync(src, dest);
}

function copyTree(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const from = path.join(src, entry.name);
    const to = path.join(dest, entry.name);
    if (entry.isDirectory()) copyTree(from, to);
    else if (entry.isFile()) fs.copyFileSync(from, to);
  }
}
