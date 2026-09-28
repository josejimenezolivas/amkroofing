"use strict";
// Shared guards for the Google API proxy routes.
//
// The browser never sees GOOGLE_MAPS_API_KEY any more — it lives only in the Vercel
// environment and is read here, server-side. These guards exist so the proxy itself
// doesn't just become the new free-for-all: they bound WHAT can be asked (service
// area) and HOW OFTEN (rate limit).
//
// Note on layering: origin checks and rate limits raise the cost of abuse, they do
// not make it impossible. The hard ceiling on the bill is the per-API daily quota
// cap set in Google Cloud Console. Set those too.

const KEY = (process.env.GOOGLE_MAPS_API_KEY || "").trim();

// Service area, as "minLat,minLon,maxLat,maxLon". Defaults to the greater Bay Area:
// requests outside it are rejected before they cost anything, so these endpoints are
// useless as a free nationwide Solar/Geocoding proxy.
const BBOX = (process.env.SERVICE_AREA_BBOX || "36.5,-123.6,38.9,-120.9")
  .split(",").map(Number);

const ALLOWED_HOSTS = (process.env.ALLOWED_ORIGINS || "amkroofing.com,www.amkroofing.com")
  .split(",").map(s => s.trim().toLowerCase()).filter(Boolean);

// Per-IP sliding window. In-memory, so it is per-instance and resets on cold start —
// a speed bump against casual scripting, not a distributed rate limiter. Swap in
// Upstash Redis (@upstash/ratelimit) if this needs to hold under a real attack.
const WINDOW_MS = Number(process.env.RATE_WINDOW_MS || 60000);
const MAX_HITS = Number(process.env.RATE_MAX_HITS || 40);
const hits = new Map();

function rateLimited(req) {
  const ip = (req.headers["x-forwarded-for"] || "").split(",")[0].trim() || "unknown";
  const now = Date.now();
  const recent = (hits.get(ip) || []).filter(t => now - t < WINDOW_MS);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 5000) for (const [k, v] of hits) if (!v.some(t => now - t < WINDOW_MS)) hits.delete(k);
  return recent.length > MAX_HITS;
}

// Same-origin check. Forgeable like any header — it only filters drive-by use of the
// endpoint from other sites, and is deliberately skipped for Vercel preview domains.
function originAllowed(req) {
  const raw = req.headers.origin || req.headers.referer || "";
  if (!raw) return false;
  let host;
  try { host = new URL(raw).hostname.toLowerCase(); } catch { return false; }
  return ALLOWED_HOSTS.includes(host) || host.endsWith(".vercel.app") || host === "localhost" || host === "127.0.0.1";
}

function inServiceArea(lat, lon) {
  return Number.isFinite(lat) && Number.isFinite(lon)
    && lat >= BBOX[0] && lat <= BBOX[2] && lon >= BBOX[1] && lon <= BBOX[3];
}

// Slippy tile (z/x/y) → lat/lon of the tile centre, so tile requests can be
// service-area checked the same way coordinates are.
function tileCentre(z, x, y) {
  const n = 2 ** z;
  const lon = ((x + 0.5) / n) * 360 - 180;
  const lat = Math.atan(Math.sinh(Math.PI * (1 - (2 * (y + 0.5)) / n))) * 180 / Math.PI;
  return { lat, lon };
}

// Runs the checks every proxy route shares. Returns true if it already responded.
function rejected(req, res, { methods = ["GET"] } = {}) {
  if (!methods.includes(req.method)) { res.status(405).json({ error: "method_not_allowed" }); return true; }
  if (!KEY) { res.status(503).json({ error: "api_key_not_configured" }); return true; }
  if (!originAllowed(req)) { res.status(403).json({ error: "forbidden_origin" }); return true; }
  if (rateLimited(req)) { res.setHeader("Retry-After", "60"); res.status(429).json({ error: "rate_limited" }); return true; }
  return false;
}

module.exports = { KEY, rejected, inServiceArea, tileCentre };
