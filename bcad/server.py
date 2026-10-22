"""Local-only browser workbench. Run with the external CAD Python environment."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import secrets
import threading
import webbrowser

from .core_client import CoreClient, KernelError
from .model import Controller, DocumentError, MAX_DOCUMENT, new_document


class WorkbenchServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(self, address, controller):
        self.controller = controller
        self.token = secrets.token_urlsafe(32)
        self.lock = threading.Lock()
        self.root = Path(__file__).resolve().parent.parent / "workbench"
        super().__init__(address, Handler)


class Handler(BaseHTTPRequestHandler):
    server_version = "B-CAD-local/0.1"

    def log_message(self, format, *args):
        pass  # no documents, tokens or file data in request logs

    def send(self, status, body, mime="application/json; charset=utf-8"):
        data = json.dumps(body, allow_nan=False).encode() if isinstance(body, (dict, list)) else body
        self.send_response(status)
        self.send_header("Content-Type", mime)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy", "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(data)

    def error(self, status, message, code="invalid_request"):
        self.send(status, {"error": {"code": code, "message": message}})

    def local_request(self):
        port = self.server.server_port
        hosts = {f"127.0.0.1:{port}", f"localhost:{port}"}
        if self.headers.get("Host") not in hosts:
            self.error(403, "Use the loopback URL printed by B-CAD")
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in {"http://" + host for host in hosts}:
            self.error(403, "Cross-origin access is disabled")
            return False
        protects_data = self.command != "GET" or self.path.startswith("/api/")
        if protects_data and self.headers.get("Sec-Fetch-Site") == "cross-site":
            self.error(403, "Cross-site access is disabled")
            return False
        return True

    def authenticated(self):
        if not self.local_request():
            return False
        if not secrets.compare_digest(self.headers.get("X-BCAD-Token", "").encode("utf-8"), self.server.token.encode("ascii")):
            self.error(403, "Missing or invalid workbench session token")
            return False
        return True

    def do_GET(self):
        if not self.local_request():
            return
        if self.path == "/api/bootstrap":
            with self.server.lock:
                self.send(200, {"token": self.server.token, "state": self.server.controller.state()})
            return
        if self.path == "/api/document":
            if self.authenticated():
                with self.server.lock:
                    self.send(200, self.server.controller.state())
            return
        assets = {"/": ("index.html", "text/html; charset=utf-8"),
                  "/index.html": ("index.html", "text/html; charset=utf-8"),
                  "/style.css": ("style.css", "text/css; charset=utf-8"),
                  "/app.js": ("app.js", "text/javascript; charset=utf-8")}
        if self.path not in assets:
            self.error(404, "Not found")
            return
        filename, mime = assets[self.path]
        try:
            data = (self.server.root / filename).read_bytes()
        except FileNotFoundError:
            self.error(404, "Workbench assets are missing")
            return
        self.send(200, data, mime)

    def do_POST(self):
        try:
            size = int(self.headers.get("Content-Length", "-1"))
            if not 0 < size <= MAX_DOCUMENT:
                raise DocumentError("Request exceeds 15 MiB or has no declared length")
            if self.headers.get("Transfer-Encoding"):
                self.error(415, "Use a bounded application/json request")
                self.close_connection = True
                return
            # Consume a bounded, declared body before rejecting authentication or
            # MIME. Closing a Windows socket with unread data can reset it before
            # the browser receives the 403/415 response.
            previous_timeout = self.connection.gettimeout()
            try:
                self.connection.settimeout(5)
                raw = self.rfile.read(size)
            finally:
                self.connection.settimeout(previous_timeout)
            if len(raw) != size:
                raise DocumentError("Incomplete request body")
            if not self.authenticated():
                self.close_connection = True
                return
            if self.headers.get("Content-Type", "").split(";")[0] != "application/json":
                self.error(415, "Use a bounded application/json request")
                self.close_connection = True
                return
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise DocumentError("Request must be a JSON object")
            with self.server.lock:
                controller = self.server.controller
                if self.path in ("/api/preview", "/api/commit"):
                    state = controller.apply(controller.candidate(payload), self.path.endswith("preview"))
                elif self.path == "/api/new":
                    state = controller.apply(new_document(payload.get("kind", "plate")), reset=True)
                elif self.path == "/api/load":
                    state = controller.apply(payload.get("document"))
                elif self.path in ("/api/undo", "/api/redo"):
                    state = controller.history(self.path.endswith("redo"))
                elif self.path == "/api/export":
                    state = controller.export(payload.get("format"))
                elif self.path == "/api/import-step":
                    state = controller.import_step(payload)
                else:
                    self.error(404, "Unknown operation")
                    return
                self.send(200, state)
        except (DocumentError, ValueError, UnicodeError, TypeError, RecursionError, TimeoutError) as exc:
            self.error(400, str(exc))
        except KernelError as exc:
            self.error(422, str(exc), exc.code)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--core-python", help="External Python with requirements-core.txt installed")
    args = parser.parse_args()
    controller = Controller(CoreClient(args.core_python))
    server = WorkbenchServer(("127.0.0.1", args.port), controller)
    url = f"http://127.0.0.1:{server.server_port}"
    print(f"B-CAD experimental workbench: {url}\nCtrl+C stops the local server.", flush=True)
    if controller.error:
        print(controller.error, flush=True)
    if not args.no_browser:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
