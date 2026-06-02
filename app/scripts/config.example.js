// Copy to config.js (gitignored) and fill in your values.
//
// NOTE: GOOGLE_MAPS_API_KEY ships to the browser and is publicly visible. Restrict it
// in Google Cloud Console (HTTP-referrer + only the APIs you use: Solar API, and
// Map Tiles API if TILE_PROVIDER = "google").
window.GOOGLE_MAPS_API_KEY = "YOUR_GOOGLE_MAPS_API_KEY";

// Satellite basemap engine:
//   "google" — Google Map Tiles API satellite (best alignment with Solar polygons; needs
//              the key above + Map Tiles API enabled + billing).
//   "osm"    — Esri World Imagery aerial (free, no key). OpenStreetMap itself has no
//              satellite layer, so the non-Google engine uses Esri's free imagery.
// If unset, defaults to "google" when a key is present, else "osm".
window.TILE_PROVIDER = "google";
