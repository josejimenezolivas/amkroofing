import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Served at amkroofing.com/forms. API calls stay under /forms/api so they
// do not collide with the marketing site's /api/solar, /api/geocode, /api/tiles.
export default defineConfig({
  base: "/forms/",
  plugins: [react()],
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
