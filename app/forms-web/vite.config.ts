import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

import react from "@vitejs/plugin-react";
import { defineConfig, type Plugin } from "vite";

const SITE = fileURLToPath(new URL("..", import.meta.url));

const TYPES: Record<string, string> = {
  ".css": "text/css",
  ".geojson": "application/geo+json",
  ".html": "text/html",
  ".ico": "image/x-icon",
  ".jpg": "image/jpeg",
  ".js": "text/javascript",
  ".json": "application/json",
  ".mp4": "video/mp4",
  ".png": "image/png",
  ".svg": "image/svg+xml",
  ".webmanifest": "application/manifest+json",
  ".webp": "image/webp",
};

/**
 * Serves the marketing site at / in dev, so links home stay on this server.
 * Only what scripts/build.js ships to dist/; /api/* functions still 404 here.
 */
function marketingSite(): Plugin {
  const shipped = (rel: string) =>
    ["index.html", "favicon.ico", "site.webmanifest", "scripts/config.js"].includes(rel) ||
    rel.startsWith("assets/");

  return {
    name: "marketing-site",
    configureServer(server) {
      server.middlewares.use((req, res, next) => {
        const pathname = decodeURIComponent(new URL(req.url ?? "/", "http://dev").pathname);
        if (pathname === "/forms") {
          res.writeHead(302, { Location: "/forms/" }).end();
          return;
        }
        const rel = pathname === "/" ? "index.html" : pathname.slice(1);
        const file = path.join(SITE, rel);
        if (!shipped(rel) || !file.startsWith(SITE) || !fs.statSync(file, { throwIfNoEntry: false })?.isFile()) {
          return next();
        }
        res.setHeader("Content-Type", TYPES[path.extname(file)] ?? "application/octet-stream");
        fs.createReadStream(file).pipe(res);
      });
    },
  };
}

// Served at amkroofing.com/forms. API calls stay under /forms/api so they
// do not collide with the marketing site's /api/solar, /api/geocode, /api/tiles.
export default defineConfig({
  base: "/forms/",
  plugins: [react(), marketingSite()],
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      "/forms/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        // The API builds Google's redirect URI from X-Forwarded-Host/Proto.
        xfwd: true,
      },
    },
  },
});
