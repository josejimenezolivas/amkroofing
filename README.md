# Amk Roofing

[amkroofing.com](https://amkroofing.com)

## Run locally

The site is static HTML — no build step and no dependencies to install. It does need to be
served over HTTP, because the roof scan fetches JSON from `assets/scans/`, which browsers
block on `file://` URLs. Opening `index.html` directly renders the page but silently fails
the scan.

```bash
cd app
python3 -m http.server 4321
```

Then open <http://127.0.0.1:4321>.
