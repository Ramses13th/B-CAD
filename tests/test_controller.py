"""Document transactions and the real imported-source controller path."""

import copy
import json
import math
import subprocess
import sys
import unittest
from unittest import mock

from bcad.core_client import CoreClient, KernelError
from bcad.model import Controller, DocumentError, new_document, parse_document, validate_document


class RecordingCore:
    def __init__(self):
        self.calls = []
        self.fail = False

    def request(self, op, **payload):
        self.calls.append((op, copy.deepcopy(payload)))
        if self.fail:
            raise KernelError("Fixture kernel rejected the candidate", "invalid_geometry")
        return {"kind": payload.get("part", {}).get("kind", "imported"), "test_payload": copy.deepcopy(payload), "metrics": {"valid": True}}


class TransactionTests(unittest.TestCase):
    def setUp(self):
        self.core = RecordingCore()
        self.controller = Controller(self.core)

    def candidate(self, width="100 mm"):
        payload = {"kind": "plate", "parameters": {"width": width, "depth": "50 mm", "height": "8 mm", "hole_diameter": "12 mm"}}
        return self.controller.candidate(payload)

    def test_preview_is_tentative_and_commit_undo_redo_are_document_transactions(self):
        original = copy.deepcopy(self.controller.document)
        candidate = self.candidate()
        preview = self.controller.apply(candidate, preview=True)
        self.assertTrue(preview["preview"])
        self.assertEqual(self.controller.document, original)
        self.assertFalse(self.controller.undo_stack)
        committed = self.controller.apply(candidate)
        self.assertEqual(committed["document"]["part"]["parameters"]["width"], "100 mm")
        self.assertTrue(committed["history"]["can_undo"])
        undone = self.controller.history()
        self.assertEqual(undone["document"]["part"], original["part"])
        self.assertGreater(undone["document"]["revision"], committed["document"]["revision"])
        redone = self.controller.history(redo=True)
        self.assertEqual(redone["document"]["part"], candidate["part"])
        self.assertGreater(redone["document"]["revision"], undone["document"]["revision"])

    def test_failed_validation_or_native_evaluation_cannot_modify_committed_state(self):
        original = self.controller.state()
        with self.assertRaises(DocumentError):
            self.controller.apply(self.candidate("__import__('os').getcwd()"))
        self.assertEqual(self.controller.state(), original)
        self.core.fail = True
        with self.assertRaises(KernelError):
            self.controller.apply(self.candidate())
        self.assertEqual(self.controller.state(), original)
        self.assertFalse(self.controller.undo_stack)

    def test_unit_expressions_cross_worker_boundary_as_numeric_millimeters(self):
        candidate = self.candidate("2 in + 1 cm")
        candidate["part"]["parameters"]["depth"] = "width / 2"
        self.controller.apply(candidate)
        op, sent = self.core.calls[-1]
        self.assertEqual(op, "evaluate")
        self.assertAlmostEqual(sent["part"]["values"]["width"], 60.8)
        self.assertAlmostEqual(sent["part"]["values"]["depth"], 30.4)
        self.assertEqual(sent["revision"], candidate["revision"])

    def test_save_reload_keeps_parameter_expressions_and_identity(self):
        self.controller.apply(self.candidate("2 in + 1 cm"))
        saved = json.dumps(self.controller.document)
        restored = parse_document(saved)
        self.assertEqual(restored, self.controller.document)
        self.assertEqual(restored["part"]["parameters"]["width"], "2 in + 1 cm")
        malformed = copy.deepcopy(restored)
        malformed["schema_version"] = 2
        with self.assertRaises(DocumentError):
            parse_document(json.dumps(malformed))
        self.assertEqual(restored, self.controller.document)

    def test_new_edit_after_undo_discards_redo_and_bounds_history(self):
        for number in range(25):
            self.controller.apply(self.candidate(f"{100 + number} mm"))
        self.assertEqual(len(self.controller.undo_stack), 20)
        self.controller.history()
        self.assertTrue(self.controller.redo_stack)
        self.controller.apply(self.candidate("90 mm"))
        self.assertFalse(self.controller.redo_stack)

    def test_missing_kernel_is_visible_and_later_success_recovers(self):
        core = RecordingCore()
        core.fail = True
        controller = Controller(core)
        self.assertFalse(controller.state()["kernel_available"])
        self.assertIn("rejected", controller.state()["error"])
        core.fail = False
        self.assertTrue(controller.apply(new_document())["kernel_available"])
        self.assertIsNone(controller.error)

    def test_malformed_schema_and_unhashable_part_kinds_are_rejected_as_document_errors(self):
        for kind in ([], {}, 1, None):
            with self.subTest(kind=kind):
                with self.assertRaises(DocumentError):
                    new_document(kind)
                document = new_document()
                document["part"]["kind"] = kind
                with self.assertRaises(DocumentError):
                    validate_document(document)
        for name, value in (("schema_version", True), ("schema_version", []), ("revision", -1), ("revision", True), ("units", []), ("part", None), ("document_id", [])):
            document = new_document()
            document[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(DocumentError):
                validate_document(document)
        with self.assertRaises(DocumentError):
            parse_document("[" * 1100 + "0" + "]" * 1100)


class WorkerBoundaryTests(unittest.TestCase):
    def test_protocol_and_revision_mismatch_are_rejected(self):
        for changed in ({"protocol": 2}, {"revision": 999}):
            def response(*args, **kwargs):
                sent = json.loads(kwargs["input"])
                reply = {"protocol": 1, "id": sent["id"], "revision": sent["revision"], "ok": True, "result": {"untrusted": True}, **changed}
                return subprocess.CompletedProcess(args[0], 0, json.dumps(reply), "")
            with self.subTest(changed=changed), mock.patch("bcad.core_client.subprocess.run", side_effect=response):
                with self.assertRaises(KernelError):
                    CoreClient().request("ping", revision=3)


class NativeControllerTests(unittest.TestCase):
    def test_import_save_reopen_and_reexport_keep_exact_source_and_volume(self):
        controller = Controller(CoreClient(sys.executable))
        self.assertIsNone(controller.error)
        original_volume = controller.result["metrics"]["volume_mm3"]
        step = controller.export("step")
        controller.import_step({"filename": "plate.step", "data_base64": step["data_base64"]})
        self.assertEqual(controller.document["part"]["kind"], "imported")
        self.assertEqual(controller.document["part"]["parameters"], {})
        self.assertAlmostEqual(controller.result["metrics"]["volume_mm3"], original_volume, places=5)
        restored = parse_document(json.dumps(controller.document))
        controller.apply(restored)
        reexport = controller.export("step")
        self.assertEqual(reexport["kind"], "imported")
        self.assertAlmostEqual(reexport["metrics"]["volume_mm3"], (80 * 50 - math.pi * 6**2) * 8, places=5)


if __name__ == "__main__":
    unittest.main()
