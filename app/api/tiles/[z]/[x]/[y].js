"use strict";
// GET /api/tiles/{z}/{x}/{y}  →  satellite tile bytes from the Map Tiles API.
//
// The Map Tiles session token is created and held HERE, server-side. The browser
// used to create the session itself (which required the key) and then append the
// key to every single tile URL — so every tile request published the key.
//
// Tiles are the most expensive thing this key can buy, so this route is the most
// tightly bounded: fixed zoom range, service-area check on the tile centre, and a
// long CDN cache so repeat views of the same roof cost nothing.
const { KEY, rejected, inServiceArea, tileCentre } = require("../../../_lib/guard");

const MIN_ZOOM = 15, MAX_ZOOM = 21;

// Session tokens last ~2 weeks; cache in module scope and refresh on expiry or
// rejection. Survives across invocations on a warm instance.
let session = null, sessionAt = 0;
const SESSION_TTL_MS = 6 * 24 * 60 * 60 * 1000;

async function getSession(force) {
  if (!force && session && Date.now() - sessionAt < SESSION_TTL_MS) return session;
  const r = await fetch(`https://tile.googleapis.com/v1/createSession?key=${encodeURIComponent(KEY)}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ mapType: "satellite", language: "en-US", region: "US" })
  });
  if (!r.ok) return null;
  session = (await r.json()).session || null;
  sessionAt = Date.now();
  return session;
}

module.exports = async function handler(req, res) {
  if (rejected(req, res, { methods: ["GET", "HEAD"] })) return;

  // The client probes with HEAD to decide between Google tiles and the free Esri
  // fallback. Answer from the session alone — never fetch (and bill) a real tile.
  if (req.method === "HEAD") {
    const ok = await getSession(false).catch(() => null);
    return res.status(ok ? 200 : 502).end();
  }

  const z = Number(req.query.z), x = Number(req.query.x), y = Number(req.query.y);
  if (!Number.isInteger(z) || !Number.isInteger(x) || !Number.isInteger(y)) {
    return res.status(400).json({ error: "bad_tile" });
  }
  if (z < MIN_ZOOM || z > MAX_ZOOM) return res.status(400).json({ error: "zoom_out_of_range" });
  const n = 2 ** z;
  if (x < 0 || x >= n || y < 0 || y >= n) return res.status(400).json({ error: "bad_tile" });

  const { lat, lon } = tileCentre(z, x, y);
  if (!inServiceArea(lat, lon)) return res.status(403).json({ error: "outside_service_area" });

  try {
    let s = await getSession(false);
    if (!s) return res.status(502).json({ error: "session_unavailable" });

    const tileUrl = () =>
      `https://tile.googleapis.com/v1/2dtiles/${z}/${x}/${y}?session=${encodeURIComponent(s)}&key=${encodeURIComponent(KEY)}`;

    let r = await fetch(tileUrl());
    if (r.status === 401 || r.status === 403) {        // stale session → refresh once
      s = await getSession(true);
      if (!s) return res.status(502).json({ error: "session_unavailable" });
      r = await fetch(tileUrl());
    }
    if (!r.ok) return res.status(502).json({ error: "upstream_error" });

    const buf = Buffer.from(await r.arrayBuffer());
    res.setHeader("Content-Type", r.headers.get("content-type") || "image/jpeg");
    // Satellite imagery is effectively static; cache hard at the CDN so a second
    // visitor looking at the same roof never re-bills the Map Tiles API.
    res.setHeader("Cache-Control", "public, s-maxage=2592000, stale-while-revalidate=2592000, max-age=86400");
    return res.status(200).send(buf);
  } catch {
    return res.status(502).json({ error: "upstream_error" });
  }
};
