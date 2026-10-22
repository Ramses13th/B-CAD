"""Experimental exact-CAD display adapter. Native libraries stay outside Blender."""
bl_info = {"name": "B-CAD Experimental", "author": "B-CAD contributors",
           "version": (0, 1, 0), "blender": (5, 1, 0),
           "location": "View3D > Sidebar > B-CAD", "category": "3D View",
           "description": "Parametric primitives through an isolated exact CAD worker"}

import json
import os
from pathlib import Path
import tempfile
import bpy
from bpy.props import EnumProperty, PointerProperty, StringProperty
from bpy_extras.io_utils import ExportHelper, ImportHelper

try:
    from .bcad.core_client import CoreClient
    from .bcad.model import new_document, parse_document, validate_document
except ModuleNotFoundError:  # source checkout / headless development
    from bcad.core_client import CoreClient
    from bcad.model import new_document, parse_document, validate_document

ADDON_ID = __package__


class BCADPreferences(bpy.types.AddonPreferences):
    bl_idname = ADDON_ID
    core_python: StringProperty(name="External Python", subtype="FILE_PATH",
                               description="Python in the separate environment containing requirements-core.txt")

    def draw(self, context):
        self.layout.prop(self, "core_python")
        self.layout.label(text="Select .venv/Scripts/python.exe (Windows) or .venv/bin/python.")
        self.layout.label(text="Native CAD packages run outside Blender.")


class BCADSettings(bpy.types.PropertyGroup):
    kind: EnumProperty(name="Part", items=[("plate", "Drilled plate", ""), ("box", "Box", ""), ("cylinder", "Cylinder", "")])
    width: StringProperty(name="Width", default="80 mm")
    depth: StringProperty(name="Depth", default="50 mm")
    height: StringProperty(name="Height", default="8 mm")
    diameter: StringProperty(name="Diameter", default="40 mm")
    hole_diameter: StringProperty(name="Hole diameter", default="12 mm")


def apply_document(context, document):
    """Evaluate first; update Blender only after a complete successful result."""
    values = validate_document(document)
    preferences = context.preferences.addons[ADDON_ID].preferences
    python = bpy.path.abspath(preferences.core_python)
    if not python or not Path(python).is_file():
        raise ValueError("Set External Python in B-CAD add-on preferences first")
    client = CoreClient(python)
    if values is None:
        result = client.request("import_step", data_base64=document["part"]["source"]["data_base64"])
    else:
        result = client.request("evaluate", part={"kind": document["part"]["kind"], "values": values})
    vertices = [[coordinate * 0.001 for coordinate in point] for point in result["mesh"]["vertices"]]
    mesh = bpy.data.meshes.new("B-CAD display cache")
    mesh.from_pydata(vertices, [], result["mesh"]["triangles"])
    mesh.update()
    obj = next((obj for obj in context.scene.objects if obj.get("bcad_document_id") == document["document_id"]), None)
    if obj is None:
        obj = bpy.data.objects.new(document["name"], mesh)
        context.collection.objects.link(obj)
    else:
        old = obj.data
        obj.data = mesh
        if old.users == 0:
            bpy.data.meshes.remove(old)
    obj["bcad_document_id"] = document["document_id"]
    obj["bcad_display_cache"] = True
    context.scene.bcad_document = json.dumps(document, allow_nan=False)
    context.scene.bcad_metrics = json.dumps(result["metrics"], allow_nan=False)
    context.scene.unit_settings.system = "METRIC"
    context.scene.unit_settings.scale_length = 1.0
    context.scene.unit_settings.length_unit = "MILLIMETERS"
    for selected in context.selected_objects:
        selected.select_set(False)
    obj.select_set(True)
    context.view_layer.objects.active = obj
    context.view_layer.update()
    return obj


class BCAD_OT_recompute(bpy.types.Operator):
    bl_idname = "bcad.recompute"
    bl_label = "Build / Recompute"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            settings = context.scene.bcad_settings
            document = parse_document(context.scene.bcad_document) if context.scene.bcad_document else new_document(settings.kind)
            if document["part"]["kind"] == "imported":
                raise ValueError("Imported STEP is a base body. Create a new part to edit dimensions.")
            prototype = new_document(settings.kind)
            document["part"] = {"kind": settings.kind, "parameters": {key: getattr(settings, key) for key in prototype["part"]["parameters"]}}
            document["revision"] += 1
            apply_document(context, document)
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class BCAD_OT_new(bpy.types.Operator):
    bl_idname = "bcad.new_part"
    bl_label = "New Part"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        try:
            document = new_document(context.scene.bcad_settings.kind)
            for key in document["part"]["parameters"]:
                document["part"]["parameters"][key] = getattr(context.scene.bcad_settings, key)
            apply_document(context, document)
        except (ValueError, RuntimeError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class BCAD_OT_save(bpy.types.Operator, ExportHelper):
    bl_idname = "bcad.save_document"
    bl_label = "Save B-CAD Project"
    filename_ext = ".bcad"
    filter_glob: StringProperty(default="*.bcad", options={"HIDDEN"})

    def execute(self, context):
        temporary = None
        try:
            document = parse_document(context.scene.bcad_document)
            serialized = json.dumps(document, indent=2, allow_nan=False)
            target = Path(self.filepath)
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8",
                                             dir=target.parent, prefix=".bcad-",
                                             suffix=".tmp", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(serialized)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        except (ValueError, OSError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        return {"FINISHED"}


class BCAD_OT_load(bpy.types.Operator, ImportHelper):
    bl_idname = "bcad.load_document"
    bl_label = "Open B-CAD Project"
    bl_options = {"REGISTER", "UNDO"}
    filename_ext = ".bcad"
    filter_glob: StringProperty(default="*.bcad", options={"HIDDEN"})

    def execute(self, context):
        try:
            if Path(self.filepath).stat().st_size > 15 * 1024 * 1024:
                raise ValueError("Project exceeds 15 MiB")
            document = parse_document(Path(self.filepath).read_text(encoding="utf-8"))
            apply_document(context, document)
            if document["part"]["kind"] != "imported":
                context.scene.bcad_settings.kind = document["part"]["kind"]
                for key, value in document["part"]["parameters"].items():
                    setattr(context.scene.bcad_settings, key, value)
        except (ValueError, RuntimeError, OSError) as exc:
            self.report({"ERROR"}, str(exc))
            return {"CANCELLED"}
        return {"FINISHED"}


class BCAD_PT_panel(bpy.types.Panel):
    bl_label = "B-CAD · Experimental"
    bl_idname = "BCAD_PT_panel"
    bl_space_type, bl_region_type, bl_category = "VIEW_3D", "UI", "B-CAD"

    def draw(self, context):
        layout, settings = self.layout, context.scene.bcad_settings
        layout.label(text="Exact CAD · mm · isolated kernel", icon="MOD_BUILD")
        layout.prop(settings, "kind")
        keys = ("diameter", "height") if settings.kind == "cylinder" else ("width", "depth", "height")
        for key in keys:
            layout.prop(settings, key)
        if settings.kind == "plate":
            layout.prop(settings, "hole_diameter")
        layout.label(text="Expressions: width / 2, 2 in, 8 mm")
        layout.operator("bcad.recompute", icon="FILE_REFRESH")
        layout.operator("bcad.new_part", icon="ADD")
        row = layout.row(align=True)
        row.operator("bcad.load_document", text="Open", icon="FILE_FOLDER")
        row.operator("bcad.save_document", text="Save", icon="FILE_TICK")
        if context.scene.bcad_metrics:
            metrics = json.loads(context.scene.bcad_metrics)
            layout.label(text=f"Volume: {metrics['volume_mm3']:.3f} mm³")
            layout.label(text=f"Solids: {metrics['solid_count']} · Valid: {metrics['valid']}")
        layout.label(text="Mesh edits/transforms do not edit CAD.")
        layout.label(text="Web workbench: STEP/STL + full controls.")


CLASSES = (BCADPreferences, BCADSettings, BCAD_OT_recompute, BCAD_OT_new,
           BCAD_OT_save, BCAD_OT_load, BCAD_PT_panel)


def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    bpy.types.Scene.bcad_settings = PointerProperty(type=BCADSettings)
    bpy.types.Scene.bcad_document = StringProperty(default="")
    bpy.types.Scene.bcad_metrics = StringProperty(default="")


def unregister():
    for name in ("bcad_settings", "bcad_document", "bcad_metrics"):
        delattr(bpy.types.Scene, name)
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
