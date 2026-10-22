"""Run with Blender --background --factory-startup --python tests/blender_smoke.py.

BCAD_ADDON_DIR points to the extracted ZIP parent. BCAD_CORE_PYTHON is external.
Writes only to ignored work/. Tests real registration, exact recompute and storage.
"""
import json
import math
import os
from pathlib import Path
import sys
from unittest import mock
import bpy
import addon_utils

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, os.environ["BCAD_ADDON_DIR"])
addon_utils.enable("b_cad", default_set=True, persistent=True)
assert "b_cad" in bpy.context.preferences.addons
bpy.context.preferences.addons["b_cad"].preferences.core_python = os.environ["BCAD_CORE_PYTHON"]
settings = bpy.context.scene.bcad_settings
settings.kind = "plate"
assert bpy.ops.bcad.recompute() == {"FINISHED"}
obj = bpy.context.view_layer.objects.active
assert obj.get("bcad_display_cache")
assert math.isclose(obj.dimensions.x, .08, abs_tol=1e-6)
metrics = json.loads(bpy.context.scene.bcad_metrics)
assert math.isclose(metrics["volume_mm3"], (80 * 50 - math.pi * 6**2) * 8, rel_tol=1e-10)
identifier = obj["bcad_document_id"]
settings.width = "100 mm"
settings.depth = "width / 2"
assert bpy.ops.bcad.recompute() == {"FINISHED"}
assert bpy.context.view_layer.objects.active == obj
assert obj["bcad_document_id"] == identifier
assert math.isclose(obj.dimensions.x, .1, abs_tol=1e-6)
saved_document = bpy.context.scene.bcad_document
saved_mesh = obj.data
settings.hole_diameter = "300 mm"
try:
    bpy.ops.bcad.recompute()
except RuntimeError:
    pass  # Blender raises when a cancelled operator reports ERROR.
assert bpy.context.scene.bcad_document == saved_document
assert obj.data == saved_mesh
settings.hole_diameter = "12 mm"
output = ROOT / "work" / "blender-smoke"
output.mkdir(parents=True, exist_ok=True)
project = output / "plate.bcad"
assert bpy.ops.bcad.save_document(filepath=str(project)) == {"FINISHED"}
assert json.loads(project.read_text())["part"]["parameters"]["width"] == "100 mm"
saved_project_bytes = project.read_bytes()
with mock.patch("b_cad.os.replace", side_effect=OSError("Fixture: replacement failed")):
    try:
        bpy.ops.bcad.save_document(filepath=str(project))
    except RuntimeError:
        pass  # An error report raises when invoking an operator through bpy.ops.
assert project.read_bytes() == saved_project_bytes
assert not list(output.glob(".bcad-*.tmp"))
settings.width = "60 mm"
assert bpy.ops.bcad.recompute() == {"FINISHED"}
assert bpy.ops.bcad.load_document(filepath=str(project)) == {"FINISHED"}
assert settings.width == "100 mm"
blend = output / "plate.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
bpy.ops.wm.open_mainfile(filepath=str(blend))
assert json.loads(bpy.context.scene.bcad_document)["part"]["parameters"]["width"] == "100 mm"
assert bpy.ops.bcad.recompute() == {"FINISHED"}
addon_utils.disable("b_cad", default_set=True)
assert not hasattr(bpy.types.Scene, "bcad_document")
print("BCAD_BLENDER_SMOKE_PASS", bpy.app.version_string)
