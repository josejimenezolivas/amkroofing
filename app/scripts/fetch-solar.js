#!/usr/bin/env node
/**
 * Fetch Google Solar API "buildingInsights" for one or more addresses and cache
 * the results to disk so they can be inspected later and served same-origin to
 * the website (no API key in the browser, no CORS).
 *
 * Output (per address), keyed by a slug of the FULL address you pass in:
 *   app/assets/scans/<address-slug>/
 *     buildingInsights.json   raw Solar API response (what the site loads)
 *     geocode.json            raw Nominatim geocode result
 *     summary.json            human-readable digest (area, pitch, segments…)
 *     roof.geojson            bounding box + roof-segment boxes (drop into geojson.io)
 *   app/assets/scans/index.json   registry of everything cached
 *
 * Key resolution (in order):
 *   1. process.env.GOOGLE_MAPS_API_KEY        ← the real env var
 *   2. window.GOOGLE_MAPS_API_KEY in app/scripts/config.js
 *
 * Usage:
 *   GOOGLE_MAPS_API_KEY=AIza... node app/scripts/fetch-solar.js "1 Apple Park Way, Cupertino, CA"
 *   node app/scripts/fetch-solar.js "addr one" "addr two" "addr three"
 */
"use strict";
const fs = require("fs");
const path = require("path");

const SCANS_DIR = path.join(__dirname, "..", "assets", "scans");
const CONFIG_JS = path.join(__dirname, "config.js");
const M2_TO_FT2 = 10.7639;

// MUST match slugify() in app/index.html so the browser finds the cached dir.
function slugify(s) {
  return (s || "").toLowerCase().trim()
    .replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 120);
}

function resolveKey() {
  if (process.env.GOOGLE_MAPS_API_KEY) return process.env.GOOGLE_MAPS_API_KEY.trim();
  try {
    const m = fs.readFileSync(CONFIG_JS, "utf8").match(/GOOGLE_MAPS_API_KEY\s*=\s*["']([^"']+)["']/);
    if (m && !m[1].startsWith("YOUR_")) return m[1];
  } catch (e) { /* no config.js */ }
  return null;
}

async function geocode(addr) {
  const url = "https://nominatim.openstreetmap.org/search?format=json&limit=1&q=" + encodeURIComponent(addr);
  const r = await fetch(url, { headers: { "User-Agent": "amkroofing-solar-cache/1.0 (amkroofing@amkroofing.com)" } });
  const j = await r.json();
  if (!j || !j.length) return null;
  return { lat: parseFloat(j[0].lat), lon: parseFloat(j[0].lon), displayName: j[0].display_name, raw: j[0] };
}

async function solar(lat, lon, key) {
  const url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    + `?location.latitude=${lat}&location.longitude=${lon}&key=${key}`;
  const r = await fetch(url);
  const j = await r.json();
  return { ok: r.ok, status: r.status, body: j };
}

// Google Geocoding API (extra_computations=BUILDING_AND_ENTRANCES) → real building outline polygon.
async function buildingOutline(addr, key) {
  const url = "https://maps.googleapis.com/maps/api/geocode/json"
    + `?address=${encodeURIComponent(addr)}&extra_computations=BUILDING_AND_ENTRANCES&key=${key}`;
  const r = await fetch(url);
  const j = await r.json();
  const res = (j.results || [])[0];
  if (!res) return null;
  const b = (res.buildings || [])[0];
  const coords = b && b.building_outlines && b.building_outlines[0]
    && b.building_outlines[0].display_polygon && b.building_outlines[0].display_polygon.coordinates;
  const ring = coords && coords[0] ? coords[0].map(c => [c[1], c[0]]) : null; // [lng,lat] → [lat,lon]
  return { ring, placeId: b ? b.place_id : null, formatted: res.formatted_address || null };
}

function box2ring(b) { // Google {sw,ne} → GeoJSON ring [lon,lat]
  return [[b.sw.longitude, b.sw.latitude], [b.ne.longitude, b.sw.latitude],
  [b.ne.longitude, b.ne.latitude], [b.sw.longitude, b.ne.latitude], [b.sw.longitude, b.sw.latitude]];
}

function buildGeoJSON(insights) {
  const feats = [];
  if (insights.boundingBox) feats.push({
    type: "Feature", properties: { kind: "buildingBoundingBox" },
    geometry: { type: "Polygon", coordinates: [box2ring(insights.boundingBox)] }
  });
  const segs = (insights.solarPotential && insights.solarPotential.roofSegmentStats) || [];
  segs.forEach((s, i) => {
    if (!s.boundingBox) return;
    feats.push({
      type: "Feature",
      properties: {
        kind: "roofSegment", index: i,
        pitchDegrees: s.pitchDegrees, azimuthDegrees: s.azimuthDegrees,
        areaFt2: s.stats && s.stats.areaMeters2 ? +(s.stats.areaMeters2 * M2_TO_FT2).toFixed(0) : null
      },
      geometry: { type: "Polygon", coordinates: [box2ring(s.boundingBox)] }
    });
  });
  return { type: "FeatureCollection", features: feats };
}

function summarize(addr, geo, insights) {
  const sp = insights.solarPotential || {};
  const segs = sp.roofSegmentStats || [];
  let pw = 0, aw = 0;
  segs.forEach(s => { const a = (s.stats && s.stats.areaMeters2 || 0) * M2_TO_FT2; if (s.pitchDegrees != null) { pw += s.pitchDegrees * a; aw += a; } });
  return {
    address: addr,
    displayName: geo.displayName,
    location: { lat: geo.lat, lon: geo.lon },
    fetchedAt: new Date().toISOString(),
    imageryQuality: insights.imageryQuality || null,
    imageryDate: insights.imageryDate || null,
    roofAreaFt2: sp.wholeRoofStats ? Math.round(sp.wholeRoofStats.areaMeters2 * M2_TO_FT2) : null,
    avgPitchDegrees: aw ? +(pw / aw).toFixed(1) : null,
    segmentCount: segs.length
  };
}

function writeJSON(p, obj) { fs.writeFileSync(p, JSON.stringify(obj, null, 2)); }

function updateRegistry(entry) {
  const idx = path.join(SCANS_DIR, "index.json");
  let list = [];
  try { list = JSON.parse(fs.readFileSync(idx, "utf8")); } catch (e) { }
  list = list.filter(e => e.slug !== entry.slug);
  list.push(entry);
  list.sort((a, b) => a.slug.localeCompare(b.slug));
  writeJSON(idx, list);
}

async function processAddress(addr, key) {
  const slug = slugify(addr);
  if (!slug) { console.error(`  ✗ empty slug for "${addr}"`); return; }
  const dir = path.join(SCANS_DIR, slug);
  fs.mkdirSync(dir, { recursive: true });

  process.stdout.write(`• ${addr}\n  geocoding… `);
  const geo = await geocode(addr);
  if (!geo) { console.error("✗ no geocode match — skipping"); return; }
  console.log(`${geo.lat.toFixed(5)}, ${geo.lon.toFixed(5)}`);
  writeJSON(path.join(dir, "geocode.json"), geo.raw);

  process.stdout.write("  solar… ");
  const res = await solar(geo.lat, geo.lon, key);
  if (!res.ok) {
    const msg = res.body && res.body.error ? `${res.body.error.status}: ${res.body.error.message}` : `HTTP ${res.status}`;
    console.error(`✗ ${msg}`);
    writeJSON(path.join(dir, "error.json"), res.body);
    return;
  }
  const insights = res.body;
  writeJSON(path.join(dir, "buildingInsights.json"), insights);
  writeJSON(path.join(dir, "roof.geojson"), buildGeoJSON(insights));

  process.stdout.write("  outline… ");
  let outline = null;
  try { outline = await buildingOutline(addr, key); } catch (e) { }
  if (outline && outline.ring) {
    writeJSON(path.join(dir, "outline.json"), outline);
    console.log(`✓ ${outline.ring.length} vertices`);
  } else { console.log("✗ no building outline"); }

  const summary = summarize(addr, geo, insights);
  summary.outlineVertices = outline && outline.ring ? outline.ring.length : 0;
  writeJSON(path.join(dir, "summary.json"), summary);
  updateRegistry({ slug, address: addr, displayName: geo.displayName, roofAreaFt2: summary.roofAreaFt2, segmentCount: summary.segmentCount, hasOutline: !!(outline && outline.ring), fetchedAt: summary.fetchedAt });

  console.log(`  ✓ ${summary.segmentCount} segments · ${summary.roofAreaFt2} ft² · ${summary.avgPitchDegrees}°`);
  console.log(`  → assets/scans/${slug}/`);
}

(async () => {
  const key = resolveKey();
  if (!key) {
    console.error("No API key. Set GOOGLE_MAPS_API_KEY or put it in app/scripts/config.js");
    process.exit(1);
  }
  const addrs = process.argv.slice(2);
  if (!addrs.length) {
    console.error('Usage: node app/scripts/fetch-solar.js "<address>" ["<address>" …]');
    process.exit(1);
  }
  fs.mkdirSync(SCANS_DIR, { recursive: true });
  for (let i = 0; i < addrs.length; i++) {
    await processAddress(addrs[i], key);
    if (i < addrs.length - 1) await new Promise(r => setTimeout(r, 1100)); // be nice to Nominatim
  }
})().catch(e => { console.error(e); process.exit(1); });
