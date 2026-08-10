#!/usr/bin/env python3
"""
Petit serveur HTTP qui expose le binaire CLI `marina` (solveur SAT en OCaml)
sous forme d'API web consultable en ligne.

Aucune dépendance externe : uniquement la bibliothèque standard de Python.

Endpoints :
  GET  /health                 -> {"status": "ok"}
  GET  /solve?prop=<formule>   -> {"prop": ..., "result": ...}
  POST /solve  {"prop": "..."} -> {"prop": ..., "result": ...}
  GET  /                       -> petite page d'aide HTML
"""

import json
import os
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

MARINA_BIN = os.environ.get("MARINA_BIN", "/app/marina")
PORT = int(os.environ.get("PORT", "8080"))
TIMEOUT_SECONDS = float(os.environ.get("MARINA_TIMEOUT", "5"))

INDEX_HTML = """<!doctype html>
<html lang="fr">
<head><meta charset="utf-8"><title>marina - SAT solver API</title></head>
<body style="font-family: sans-serif; max-width: 640px; margin: 40px auto;">
  <h1>marina — SAT solver</h1>
  <p>API HTTP autour du solveur SAT <code>marina</code> (OCaml).</p>
  <h2>Utilisation</h2>
  <pre>GET /solve?prop=(a%26b)-%3Ec</pre>
  <pre>POST /solve
Content-Type: application/json

{"prop": "(a&b)->c"}</pre>
  <h2>Essayer</h2>
  <form action="/solve" method="get">
    <input type="text" name="prop" size="50" placeholder="(a&amp;b)-&gt;c">
    <button type="submit">Résoudre</button>
  </form>
</body>
</html>"""


def run_marina(prop: str) -> str:
    try:
        completed = subprocess.run(
            [MARINA_BIN, prop],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS,
        )
    except subprocess.TimeoutExpired:
        return None, "timeout"
    if completed.returncode != 0:
        return None, completed.stderr.strip() or "erreur inconnue"
    return completed.stdout.strip(), None


class Handler(BaseHTTPRequestHandler):
    server_version = "MarinaHTTP/1.0"

    def _send_json(self, payload: dict, status: int = 200):
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _handle_solve(self, prop):
        if prop is None or prop.strip() == "":
            self._send_json({"error": "paramètre 'prop' manquant"}, 400)
            return
        result, error = run_marina(prop)
        if error is not None:
            self._send_json({"prop": prop, "error": error}, 400)
            return
        self._send_json({"prop": prop, "result": result})

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"status": "ok"})
            return
        if parsed.path == "/solve":
            qs = parse_qs(parsed.query)
            prop = qs.get("prop", [None])[0]
            self._handle_solve(prop)
            return
        if parsed.path == "/":
            body = INDEX_HTML.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return
        self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        parsed = urlparse(self.path)
        if parsed.path != "/solve":
            self._send_json({"error": "not found"}, 404)
            return
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw or b"{}")
        except json.JSONDecodeError:
            self._send_json({"error": "JSON invalide"}, 400)
            return
        self._handle_solve(data.get("prop"))

    def log_message(self, fmt, *args):
        # Log simple sur stdout (visible via `docker logs`)
        print("%s - %s" % (self.address_string(), fmt % args))


if __name__ == "__main__":
    server = ThreadingHTTPServer(("0.0.0.0", PORT), Handler)
    print(f"marina HTTP server listening on 0.0.0.0:{PORT} (binary: {MARINA_BIN})")
    server.serve_forever()
