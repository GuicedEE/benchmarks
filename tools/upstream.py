"""Deterministic OAuth/commercetools fixture. It validates and records real SDK traffic."""
import collections
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


class Upstream(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, host="127.0.0.1"):
        super().__init__((host, 0), Handler)
        self.events = []
        self.counts = collections.Counter()
        self.lock = threading.Lock()

    def record(self, method, path, status):
        with self.lock:
            self.events.append({"method": method, "path": path, "status": status})


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def setup(self):
        super().setup()
        self.connection.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    def log_message(self, *_): pass

    def handle(self):
        try: super().handle()
        except (ConnectionResetError, BrokenPipeError): pass

    def reply(self, status, body):
        self.server.record(self.command, self.path, status)
        data = json.dumps(body).encode() if not isinstance(body, str) else body.encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        try: self.wfile.write(data)
        except (BrokenPipeError, ConnectionResetError): pass

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if self.path == "/oauth/token":
            valid = self.headers.get("Authorization") == "Basic Zml4dHVyZTpmaXh0dXJl" and b"grant_type=client_credentials" in raw
            return self.reply(200 if valid else 401, {"access_token": "fixture-token", "token_type": "Bearer", "expires_in": 3600})
        if self.path == "/benchmark/graphql":
            try: valid = "inventoryEntries" in json.loads(raw)["query"]
            except (ValueError, KeyError): valid = False
            valid &= self.headers.get("Authorization") == "Bearer fixture-token"
            return self.reply(200 if valid else 400, {"data": {"inventoryEntries": {"results": [{"availableQuantity": 40}]}}})
        self.reply(404, {"error": "unknown fixture path"})

    def do_GET(self):
        if self.path == "/benchmark":
            if self.headers.get("Authorization") != "Bearer fixture-token": return self.reply(401, {})
            return self.reply(200, {"key": "benchmark", "name": "Fixture shop", "version": 1,
                                   "createdAt": "2026-01-01T00:00:00Z", "currencies": ["ZAR"], "countries": ["ZA"], "languages": ["en"]})
        if self.path.startswith("/flaky/"):
            with self.server.lock:
                self.server.counts[self.path] += 1
                count = self.server.counts[self.path]
            return self.reply(503 if count < 3 or self.path.endswith("always") else 200, "ok")
        if self.path == "/slow":
            threading.Event().wait(0.25)
            return self.reply(200, "late")
        self.reply(404, {})
