// Copy to config.js (gitignored) for local dev, or let scripts/gen-config.js write it.
//
// This file must NEVER contain an API key. Everything that needs the Google key goes
// through the same-origin proxy in app/api/, which reads GOOGLE_MAPS_API_KEY from the
// server environment. Nothing here reaches Google directly.

// Satellite basemap engine:
//   "google" — Google Map Tiles via /api/tiles (best alignment with Solar polygons;
//              needs GOOGLE_MAPS_API_KEY in the server env + Map Tiles API enabled).
//   "osm"    — Esri World Imagery aerial (free, no key, no Google billing at all).
//              Set TILE_PROVIDER=osm to drop Map Tiles spend to zero.
window.TILE_PROVIDER = "google";
