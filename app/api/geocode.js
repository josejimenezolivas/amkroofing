"use strict";
// GET /api/geocode?address=  →  { ring, formatted }
//
// Wraps the Geocoding API's BUILDING_AND_ENTRANCES extra computation and returns
// only the building outline ring and the formatted address.
const { KEY, rejected, inServiceArea } = require("./_lib/guard");

module.exports = async function handler(req, res) {
  if (rejected(req, res)) return;

  const address = String(req.query.address || "").trim().slice(0, 200);
  if (address.length < 4) return res.status(400).json({ error: "address_required" });

  const url = "https://maps.googleapis.com/maps/api/geocode/json"
    + `?address=${encodeURIComponent(address)}`
    + "&extra_computations=BUILDING_AND_ENTRANCES"
    // Bound the geocoder to the service area so the endpoint can't be used as a
    // general-purpose geocoder for addresses this business would never quote.
    + "&components=country:US"
    + `&key=${encodeURIComponent(KEY)}`;

  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), 9000);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    clearTimeout(to);
    if (!r.ok) return res.status(502).json({ error: "upstream_error" });

    const body = await r.json();
    const result = (body.results || [])[0];
    if (!result) return res.status(404).json({ error: "not_found" });

    const loc = result.geometry && result.geometry.location;
    if (!loc || !inServiceArea(loc.lat, loc.lng)) {
      return res.status(400).json({ error: "outside_service_area" });
    }

    const b = (result.buildings || [])[0];
    const coords = b && b.building_outlines && b.building_outlines[0]
      && b.building_outlines[0].display_polygon && b.building_outlines[0].display_polygon.coordinates;
    const ring = coords && coords[0] ? coords[0].map(c => [c[1], c[0]]) : null; // [lng,lat] → [lat,lon]

    res.setHeader("Cache-Control", "public, s-maxage=86400, stale-while-revalidate=604800");
    return res.status(200).json({
      ring,
      formatted: result.formatted_address || null,
      lat: loc.lat,
      lon: loc.lng
    });
  } catch {
    clearTimeout(to);
    return res.status(504).json({ error: "upstream_timeout" });
  }
};
