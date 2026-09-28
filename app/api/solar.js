"use strict";
// GET /api/solar?lat=&lon=  →  the roof geometry the estimator needs.
//
// Returns the SHAPED result, not Google's raw buildingInsights payload. The raw
// response also carries financial analyses and panel layouts; trimming here keeps
// the endpoint from being worth scraping.
const { KEY, rejected, inServiceArea } = require("./_lib/guard");

const M2_TO_FT2 = 10.7639;

function shape(j) {
  const sp = j && j.solarPotential;
  if (!sp || !j.boundingBox) return null;
  const segs = (sp.roofSegmentStats || []).map(s => ({
    box: s.boundingBox,
    pitch: s.pitchDegrees,
    areaFt2: ((s.stats && s.stats.areaMeters2) || 0) * M2_TO_FT2
  })).filter(s => s.box && s.box.sw && s.box.ne);
  let pw = 0, aw = 0;
  segs.forEach(s => { if (s.pitch != null) { pw += s.pitch * s.areaFt2; aw += s.areaFt2; } });
  const roofM2 = (sp.wholeRoofStats && sp.wholeRoofStats.areaMeters2) || 0;
  return {
    box: j.boundingBox,
    segs,
    roofFt2: Math.round(roofM2 * M2_TO_FT2),
    pitch: aw ? pw / aw : null,
    quality: j.imageryQuality || ""
  };
}

module.exports = async function handler(req, res) {
  if (rejected(req, res)) return;

  const lat = Number(req.query.lat), lon = Number(req.query.lon);
  if (!inServiceArea(lat, lon)) return res.status(400).json({ error: "outside_service_area" });

  const url = "https://solar.googleapis.com/v1/buildingInsights:findClosest"
    + `?location.latitude=${lat}&location.longitude=${lon}&key=${encodeURIComponent(KEY)}`;

  const ctrl = new AbortController();
  const to = setTimeout(() => ctrl.abort(), 9000);
  try {
    const r = await fetch(url, { signal: ctrl.signal });
    clearTimeout(to);
    if (!r.ok) return res.status(r.status === 404 ? 404 : 502).json({ error: "upstream_error" });
    const shaped = shape(await r.json());
    if (!shaped) return res.status(404).json({ error: "no_building_insights" });
    // Solar imagery changes on the order of months; a day of CDN cache removes
    // repeat billing for the same address entirely.
    res.setHeader("Cache-Control", "public, s-maxage=86400, stale-while-revalidate=604800");
    return res.status(200).json(shaped);
  } catch {
    clearTimeout(to);
    return res.status(504).json({ error: "upstream_timeout" });
  }
};
