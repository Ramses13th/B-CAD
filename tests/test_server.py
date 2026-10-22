"""Exercise the real local HTTP boundary without launching the heavy kernel."""

import copy
import http.client
import json
import threading
import unittest

from bcad.core_client import KernelError
from bcad.model import Controller
from bcad.server import WorkbenchServer


class FakeCore:
    def __init__(self):
        self.fail = False

    def request(self, op, **payload):
        if self.fail:
            raise KernelError("Solid construction failed", "invalid_geometry")
        return {"kind": payload.get("part", {}).get("kind", "imported"), "metrics": {"valid": True}, "fixture": payload}


class LocalWorkbenchTests(unittest.TestCase):
    def setUp(self):
        self.core = FakeCore()
        self.controller = Controller(self.core)
        self.server = WorkbenchServer(("127.0.0.1", 0), self.controller)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.port = self.server.server_port

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=5)

    def send(self, method, path, payload=None, token=True, headers=None):
        connection = http.client.HTTPConnection("127.0.0.1", self.port, timeout=5)
        request_headers = {"Content-Type": "application/json"}
        if token:
            request_headers["X-BCAD-Token"] = self.server.token
        request_headers.update(headers or {})
        connection.request(method, path, None if payload is None else json.dumps(payload), request_headers)
        response = connection.getresponse()
        data = response.read()
        body = json.loads(data) if "application/json" in response.getheader("Content-Type", "") else data.decode("utf-8")
        result = (response.status, body, dict(response.getheaders()))
        connection.close()
        return result

    def payload(self, width="100 mm"):
        return {"kind": "plate", "parameters": {"width": width, "depth": "50 mm", "height": "8 mm", "hole_diameter": "12 mm"}}

    def test_bootstrap_and_authenticated_document_work_without_caching(self):
        status, body, headers = self.send("GET", "/api/bootstrap", token=False)
        self.assertEqual(status, 200)
        self.assertEqual(body["token"], self.server.token)
        self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(headers["Referrer-Policy"], "no-referrer")
        self.assertEqual(self.send("GET", "/api/document")[0], 200)
        self.assertEqual(self.send("GET", "/api/document", token=False)[0], 403)

    def test_host_origin_and_cross_site_guards_cover_bootstrap(self):
        for headers in ({"Host": "attacker.example"}, {"Origin": "https://attacker.example"}, {"Sec-Fetch-Site": "cross-site"}):
            with self.subTest(headers=headers):
                status, body, _ = self.send("GET", "/api/bootstrap", token=False, headers=headers)
                self.assertEqual(status, 403)
                self.assertNotIn("token", body)

    def test_external_browser_navigation_can_load_static_ui_without_api_access(self):
        status, body, _ = self.send("GET", "/", token=False, headers={"Sec-Fetch-Site": "cross-site"})
        self.assertEqual(status, 200)
        self.assertIn("B-CAD", body)
        self.assertNotIn(self.server.token, body)
        self.assertEqual(self.send("GET", "/api/bootstrap", token=False, headers={"Sec-Fetch-Site": "cross-site"})[0], 403)

    def test_preview_commit_undo_redo_and_failed_edit_through_http(self):
        original = copy.deepcopy(self.controller.document)
        status, body, _ = self.send("POST", "/api/preview", self.payload())
        self.assertEqual(status, 200)
        self.assertTrue(body["preview"])
        self.assertEqual(self.controller.document, original)
        self.assertEqual(self.send("POST", "/api/commit", self.payload())[0], 200)
        self.assertEqual(self.controller.document["part"]["parameters"]["width"], "100 mm")
        self.assertEqual(self.send("POST", "/api/undo", {})[0], 200)
        self.assertEqual(self.controller.document["part"], original["part"])
        self.assertEqual(self.send("POST", "/api/redo", {})[0], 200)
        committed = copy.deepcopy(self.controller.document)
        self.core.fail = True
        status, body, _ = self.send("POST", "/api/commit", self.payload("110 mm"))
        self.assertEqual(status, 422)
        self.assertEqual(body["error"]["code"], "invalid_geometry")
        self.assertEqual(self.controller.document, committed)
        self.core.fail = False
        self.assertEqual(self.send("POST", "/api/commit", self.payload("110 mm"))[0], 200)
        self.assertEqual(self.controller.document["part"]["parameters"]["width"], "110 mm")

    def test_bad_documents_and_unknown_routes_preserve_document(self):
        original = copy.deepcopy(self.controller.document)
        malformed = copy.deepcopy(original)
        malformed["schema_version"] = 2
        self.assertEqual(self.send("POST", "/api/load", {"document": malformed})[0], 400)
        self.assertEqual(self.send("POST", "/api/commit", self.payload("1 / 0"))[0], 400)
        cyclic = self.payload("depth")
        cyclic["parameters"]["depth"] = "width"
        self.assertEqual(self.send("POST", "/api/commit", cyclic)[0], 400)
        self.assertEqual(self.send("POST", "/api/commit", self.payload("__import__('os').getcwd()"))[0], 400)
        self.assertEqual(self.send("POST", "/api/new", {"kind": []})[0], 400)
        self.assertEqual(self.send("POST", "/api/missing", {})[0], 404)
        self.assertEqual(self.send("GET", "/../../AGENTS.md")[0], 404)
        self.assertEqual(self.controller.document, original)

    def test_mutations_require_token_and_json(self):
        original = copy.deepcopy(self.controller.document)
        for _ in range(3):
            self.assertEqual(self.send("POST", "/api/commit", self.payload(), token=False)[0], 403)
        self.assertEqual(self.send("POST", "/api/commit", self.payload(), headers={"X-BCAD-Token": "caf\u00e9"})[0], 403)
        self.assertEqual(self.send("POST", "/api/commit", self.payload(), headers={"Content-Type": "text/plain"})[0], 415)
        self.assertEqual(self.controller.document, original)


if __name__ == "__main__":
    unittest.main()
