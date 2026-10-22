"""Analytic geometry, exact exchange, and the real subprocess boundary."""

import base64
import json
import math
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import unittest

from bcad import kernel_worker as worker


ROOT = Path(__file__).resolve().parents[1]


def request(op="evaluate", kind="plate", values=None, **extra):
    result = {
        "protocol": 1,
        "id": "geometry-test",
        "revision": 7,
        "op": op,
        "part": {"kind": kind, "values": values or {"width": 80, "depth": 50, "height": 8, "hole_diameter": 12}},
    }
    result.update(extra)
    if "data_base64" in result:
        result.pop("part", None)
    return result


class ExactKernelTests(unittest.TestCase):
    def test_plate_matches_independent_analytic_properties(self):
        result = worker.execute(request())
        metrics = result["metrics"]
        self.assertTrue(metrics["valid"])
        self.assertEqual(metrics["solid_count"], 1)
        self.assertEqual(metrics["bounds_mm"], {"x": 80, "y": 50, "z": 8})
        self.assertAlmostEqual(metrics["volume_mm3"], (80 * 50 - math.pi * 6**2) * 8, places=6)
        expected_area = 2 * (80 * 50 - math.pi * 6**2) + 2 * (80 + 50) * 8 + 2 * math.pi * 6 * 8
        self.assertAlmostEqual(metrics["area_mm2"], expected_area, places=6)
        for actual, expected in zip(metrics["center_mm"], (0, 0, 4)):
            self.assertAlmostEqual(actual, expected, places=8)
        self.assertTrue(result["mesh"]["triangles"])
        self.assertEqual(len(result["features"]), 2)

    def test_primitives_have_analytic_bounds_volume_and_topology(self):
        cases = [
            ("box", {"width": 20, "depth": 30, "height": 5}, 3000, {"x": 20, "y": 30, "z": 5}, 6),
            ("cylinder", {"diameter": 10, "height": 7}, math.pi * 25 * 7, {"x": 10, "y": 10, "z": 7}, 3),
        ]
        for kind, values, volume, bounds, face_count in cases:
            with self.subTest(kind=kind):
                result = worker.execute(request(kind=kind, values=values))
                self.assertAlmostEqual(result["metrics"]["volume_mm3"], volume, places=7)
                self.assertEqual(result["metrics"]["bounds_mm"], bounds)
                self.assertEqual(result["metrics"]["face_count"], face_count)

    def test_tessellation_changes_preview_without_changing_exact_geometry(self):
        coarse = worker.execute(request(tessellation={"linear": 1, "angular": 0.7}))
        fine = worker.execute(request(tessellation={"linear": 0.01, "angular": 0.05}))
        self.assertGreater(len(fine["mesh"]["triangles"]), len(coarse["mesh"]["triangles"]))
        self.assertEqual(coarse["metrics"], fine["metrics"])

    def test_display_triangle_winding_faces_outward(self):
        cases = [
            ("box", {"width": 80, "depth": 50, "height": 8}),
            ("plate", {"width": 80, "depth": 50, "height": 8, "hole_diameter": 12}),
            ("cylinder", {"diameter": 40, "height": 20}),
        ]
        for kind, values in cases:
            with self.subTest(kind=kind):
                result = worker.execute(request(kind=kind, values=values))
                vertices = result["mesh"]["vertices"]
                signed_volume = 0
                top_count = bottom_count = 0
                for indices in result["mesh"]["triangles"]:
                    a, b, c = [vertices[index] for index in indices]
                    normal_z = (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
                    if all(abs(point[2] - values["height"]) < 1e-8 for point in (a, b, c)):
                        self.assertGreater(normal_z, 0)
                        top_count += 1
                    if all(abs(point[2]) < 1e-8 for point in (a, b, c)):
                        self.assertLess(normal_z, 0)
                        bottom_count += 1
                    signed_volume += (a[0] * (b[1] * c[2] - b[2] * c[1]) + a[1] * (b[2] * c[0] - b[0] * c[2]) + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
                self.assertGreater(top_count, 0)
                self.assertGreater(bottom_count, 0)
                self.assertGreater(signed_volume, 0)
                self.assertAlmostEqual(signed_volume, result["metrics"]["volume_mm3"], delta=result["metrics"]["volume_mm3"] * 0.01)

    def test_step_round_trip_preserves_exact_properties(self):
        native = worker.execute(request())
        exported = worker.execute(request(op="export_step"))
        step = base64.b64decode(exported["data_base64"], validate=True)
        self.assertIn(b"ISO-10303-21", step)
        self.assertIn(b"SI_UNIT(.MILLI.,.METRE.)", step)
        imported = worker.execute(request(op="import_step", data_base64=exported["data_base64"]))
        self.assertEqual(imported["kind"], "imported")
        self.assertEqual(imported["metrics"]["solid_count"], 1)
        self.assertTrue(imported["metrics"]["valid"])
        for name in ("volume_mm3", "area_mm2"):
            self.assertAlmostEqual(imported["metrics"][name], native["metrics"][name], places=5)
        for axis in "xyz":
            self.assertAlmostEqual(imported["metrics"]["bounds_mm"][axis], native["metrics"]["bounds_mm"][axis], places=6)
        self.assertTrue(imported["mesh"]["triangles"])

    def test_stl_has_binary_facets_and_expected_millimeter_bounds(self):
        exported = worker.execute(request(op="export_stl", kind="box", values={"width": 20, "depth": 30, "height": 5}))
        data = base64.b64decode(exported["data_base64"])
        count = struct.unpack_from("<I", data, 80)[0]
        self.assertEqual(len(data), 84 + 50 * count)
        self.assertEqual(count, 12)
        points = []
        for index in range(count):
            points.extend(struct.unpack_from("<3f", data, 84 + index * 50 + 12 + vertex * 12) for vertex in range(3))
        bounds = [max(point[axis] for point in points) - min(point[axis] for point in points) for axis in range(3)]
        self.assertEqual(bounds, [20, 30, 5])

    def test_step_import_preserves_all_roots_and_converts_declared_units(self):
        cq = worker.cadquery()
        first = cq.Workplane().box(2, 3, 1, centered=(True, True, False)).val()
        second = cq.Workplane().box(1, 1, 1, centered=(True, True, False)).translate((5, 0, 0)).val()
        model = cq.Compound.makeCompound([first, second])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "centimeter-bodies.step"
            model.exportStep(str(path), unit="CM", outputUnit="CM")
            data = base64.b64encode(path.read_bytes()).decode()
        imported = worker.execute(request(op="import_step", data_base64=data))
        self.assertEqual(imported["metrics"]["solid_count"], 2)
        self.assertAlmostEqual(imported["metrics"]["volume_mm3"], 7000, places=5)
        self.assertAlmostEqual(imported["metrics"]["bounds_mm"]["z"], 10, places=6)

    def test_imported_exact_source_can_be_reexported_without_mesh_conversion(self):
        source = worker.execute(request(op="export_step"))["data_base64"]
        exported = worker.execute(request(op="export_step", data_base64=source))
        reimported = worker.execute(request(op="import_step", data_base64=exported["data_base64"]))
        self.assertEqual(exported["kind"], "imported")
        self.assertAlmostEqual(reimported["metrics"]["volume_mm3"], (80 * 50 - math.pi * 6**2) * 8, places=5)
        stl = worker.execute(request(op="export_stl", data_base64=source))
        self.assertGreater(len(base64.b64decode(stl["data_base64"])), 84)
        conflict = request()
        conflict["data_base64"] = source
        self.assertFalse(worker.respond(conflict)["ok"])

    def test_unsafe_or_degenerate_inputs_fail_explicitly(self):
        malformed = [
            request(values={"width": -1, "depth": 50, "height": 8, "hole_diameter": 12}),
            request(values={"width": True, "depth": 50, "height": 8, "hole_diameter": 12}),
            request(values={"width": float("nan"), "depth": 50, "height": 8, "hole_diameter": 12}),
            request(values={"width": 10, "depth": 10, "height": 8, "hole_diameter": 12}),
            request(values={"width": 80, "depth": 50, "height": 8, "hole_diameter": 0}),
            request(kind="mesh"),
            request(tessellation={"linear": 0}),
            request(protocol=2),
            request(revision=True),
            request(op="import_step", data_base64="not base64"),
            request(op="import_step", data_base64=base64.b64encode(b"not a STEP file").decode()),
        ]
        for data in malformed:
            with self.subTest(data=data):
                reply = worker.respond(data)
                self.assertFalse(reply["ok"])
                self.assertIn("code", reply["error"])
                self.assertNotEqual(reply["error"]["code"], "kernel_error")

    def test_real_worker_protocol_stays_json_during_native_step_export(self):
        messages = [request(op="ping"), request(op="export_step"), request(protocol=999), request(kind="cylinder", values={"diameter": 12, "height": 5})]
        completed = subprocess.run(
            [sys.executable, "-m", "bcad.kernel_worker"],
            input="\n".join(json.dumps(message) for message in messages) + "\n",
            capture_output=True, text=True, cwd=ROOT, timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        replies = [json.loads(line) for line in completed.stdout.splitlines()]
        self.assertEqual(len(replies), 4)
        self.assertTrue(replies[0]["ok"], completed.stderr)
        self.assertEqual(replies[0]["result"]["kernel"]["CadQuery"], "2.8.0")
        self.assertTrue(replies[1]["ok"], completed.stderr)
        self.assertFalse(replies[2]["ok"])
        self.assertTrue(replies[3]["ok"], completed.stderr)
        self.assertEqual(replies[3]["revision"], 7)

    def test_once_processes_only_first_request(self):
        completed = subprocess.run(
            [sys.executable, "-m", "bcad.kernel_worker", "--once"],
            input=json.dumps(request()) + "\n" + json.dumps(request()) + "\n",
            capture_output=True, text=True, cwd=ROOT, timeout=120,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertEqual(len(completed.stdout.splitlines()), 1)
        self.assertTrue(json.loads(completed.stdout)["ok"], completed.stderr)


if __name__ == "__main__":
    unittest.main()
