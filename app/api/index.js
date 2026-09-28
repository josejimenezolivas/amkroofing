"use strict";
// Entrypoint for the `api` service in vercel.json.
//
// Under Vercel Services a Node service is one function receiving plain Node
// req/res: no file-system routing and no request helpers. This file restores
// the routing and the few helpers the handlers use, so each handler stays a
// standalone (req, res) function.
const geocode = require("./geocode");
const solar = require("./solar");
const tile = require("./tiles/[z]/[x]/[y]");

const TILE_PATH = /^\/api\/tiles\/(\d+)\/(\d+)\/(\d+)\/?$/;

function addHelpers(req, res, url) {
  req.query = Object.fromEntries(url.searchParams);
  res.status = (code) => {
    res.statusCode = code;
    return res;
  };
  res.json = (body) => {
    res.setHeader("Content-Type", "application/json; charset=utf-8");
    res.end(JSON.stringify(body));
    return res;
  };
  res.send = (body) => {
    res.end(body);
    return res;
  };
}

module.exports = async function handler(req, res) {
  const url = new URL(req.url, "http://localhost");
  addHelpers(req, res, url);

  const path = url.pathname.replace(/\/$/, "");
  if (path === "/api/solar") return solar(req, res);
  if (path === "/api/geocode") return geocode(req, res);

  const t = TILE_PATH.exec(url.pathname);
  if (t) {
    [req.query.z, req.query.x, req.query.y] = t.slice(1);
    return tile(req, res);
  }

  return res.status(404).json({ error: "not_found" });
};
