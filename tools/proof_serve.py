#!/usr/bin/env python3
"""
proof_serve.py — serve the proof copies and collect the corrections you click.

  python3 tools/proof_serve.py                  # http://127.0.0.1:8765/  (this machine)
  python3 tools/proof_serve.py --lan            # also reachable from your phone on the
                                                # same Wi-Fi: it prints the address

Serves scratch/proof/ (the pages tools/proof_copy.py writes). A page that is
served rather than opened as a file POSTs each queued correction here, and it is
appended to scratch/proof/corrections.jsonl — one JSON object per line: id, doc,
section, value, verdict, detail, context, suggested, note, ts. Nothing is applied:
a session reads the queue with tools/proof_corrections.py, verifies each item
against the committed CSVs, edits through odt_edit, and marks it done.

Standard library only. Ctrl-C stops it. Not a gate, not part of the pipeline.
"""
from __future__ import annotations

__version__ = "1.1.0"  # Hollingham (2026) — 2026-09-20. /__queue returns done items
#   too (flagged done=true), so the page can retire them from the browser's queue.
# v1.0.0  # Hollingham (2026) — 2026-09-20.

import argparse
import json
import pathlib
import socket
import sys
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

REPO = pathlib.Path(__file__).resolve().parents[1]
ROOT = REPO / "scratch" / "proof"
QUEUE = ROOT / "corrections.jsonl"


def _read_queue():
    if not QUEUE.exists():
        return []
    out = []
    for line in QUEUE.read_text(encoding="utf8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                pass
    return out


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *a, **k):
        super().__init__(*a, directory=str(ROOT), **k)

    def log_message(self, fmt, *args):          # one quiet line per request
        sys.stderr.write("  %s %s\n" % (self.command, self.path.split("?")[0]))

    def _json(self, obj, code=200):
        body = json.dumps(obj).encode("utf8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/__queue":
            doc = parse_qs(u.query).get("doc", [None])[0]
            items = [it for it in _read_queue() if (doc is None or it.get("doc") == doc)]   # done ones included: the page retires them
            return self._json(items)
        if u.path == "/":
            self.path = "/index.html"
        return super().do_GET()

    def do_POST(self):
        if urlparse(self.path).path != "/__correct":
            return self._json({"error": "unknown endpoint"}, 404)
        n = int(self.headers.get("Content-Length", "0"))
        try:
            item = json.loads(self.rfile.read(n).decode("utf8"))
        except ValueError:
            return self._json({"error": "bad json"}, 400)
        keep = {k: item.get(k, "") for k in ("id", "doc", "section", "value", "verdict",
                                             "detail", "context", "suggested", "note", "ts")}
        ROOT.mkdir(parents=True, exist_ok=True)
        with QUEUE.open("a", encoding="utf8") as fh:
            fh.write(json.dumps(keep, ensure_ascii=False) + "\n")
        print(f"  queued  {keep['doc']} §{keep['section'][:30]}  {keep['value']!r} -> {keep['suggested']!r}  {keep['note'][:60]}")
        return self._json({"ok": True, "queued": len(_read_queue())})


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--lan", action="store_true", help="listen on every interface so a phone on the same Wi-Fi can open it")
    a = ap.parse_args()
    if not ROOT.exists():
        sys.exit(f"{ROOT} does not exist — run python3 tools/proof_copy.py report9 first")
    host = "0.0.0.0" if a.lan else "127.0.0.1"
    srv = ThreadingHTTPServer((host, a.port), Handler)
    print(f"proof_serve {__version__} — serving {ROOT.relative_to(REPO)}/  queue: {QUEUE.relative_to(REPO)}")
    print(f"  open  http://127.0.0.1:{a.port}/")
    if a.lan:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect(("10.255.255.255", 1)); ip = s.getsockname()[0]; s.close()
        except OSError:
            ip = socket.gethostbyname(socket.gethostname())
        print(f"  phone http://{ip}:{a.port}/   (same Wi-Fi; the laptop's firewall must allow the port)")
    print("  Ctrl-C to stop")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
