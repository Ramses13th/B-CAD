"""Experimental exact CAD worker; JSON lines in/out, millimeters throughout.

Run with ``python -m bcad.kernel_worker``; ``--once`` exits after one request.
Only this independent interpreter imports CadQuery and its native libraries.
"""

from __future__ import annotations

import argparse
import base64
import binascii
import importlib.metadata
import json
import math
import os
from pathlib import Path
import sys
import tempfile


PROTOCOL = 1
MAX_STEP_BYTES = 10 * 1024 * 1024
MAX_REQUEST_BYTES = 14 * 1024 * 1024
MAX_DIMENSION_MM = 100_000.0
MIN_DIMENSION_MM = 0.01
MAX_MESH_TRIANGLES = 200_000
MAX_IMPORT_FACES = 2_000
_cq = None


class KernelInputError(ValueError):
    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def cadquery():
    global _cq
    if _cq is None:
        import cadquery as cq

        _cq = cq
    return _cq


def kernel_metadata() -> dict:
    cq = cadquery()
    import OCP

    return {
        "name": "OCCT",
        "version": ".".join(OCP.__version__.split(".")[:3]),
        "version_source": "OCP runtime build version prefix",
        "CadQuery": cq.__version__,
        "OCP": importlib.metadata.version("cadquery-ocp"),
        "OCP_runtime": OCP.__version__,
    }


def number(value, name: str, low: float, high: float, code="invalid_part") -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise KernelInputError(code, f"{name} must be a finite number.")
    try:
        result = float(value)
    except (ValueError, OverflowError):
        raise KernelInputError(code, f"{name} must be a finite number.") from None
    if not math.isfinite(result) or not low <= result <= high:
        raise KernelInputError(code, f"{name} must be between {low:g} and {high:g}.")
    return result


def tessellation_settings(request: dict) -> tuple[float, float]:
    settings = request.get("tessellation", {})
    if not isinstance(settings, dict) or set(settings) - {"linear", "angular"}:
        raise KernelInputError("invalid_tessellation", "Expected linear/angular tessellation settings.")
    return (
        number(settings.get("linear", 0.2), "linear tessellation (mm)", 0.01, 5.0, "invalid_tessellation"),
        number(settings.get("angular", 0.2), "angular tessellation (radians)", 0.02, 1.0, "invalid_tessellation"),
    )


def build_part(part: dict):
    if not isinstance(part, dict) or set(part) != {"kind", "values"}:
        raise KernelInputError("invalid_part", "Part must contain kind and values.")
    kind = part["kind"]
    expected = {
        "box": {"width", "depth", "height"},
        "plate": {"width", "depth", "height", "hole_diameter"},
        "cylinder": {"diameter", "height"},
    }
    if not isinstance(kind, str) or kind not in expected:
        raise KernelInputError("invalid_part", "Supported part kinds: box, plate, cylinder.")
    values = part["values"]
    if not isinstance(values, dict) or set(values) != expected[kind]:
        raise KernelInputError("invalid_part", f"{kind} requires exactly {', '.join(sorted(expected[kind]))}.")
    values = {key: number(value, key, MIN_DIMENSION_MM, MAX_DIMENSION_MM) for key, value in values.items()}
    if kind == "plate" and values["hole_diameter"] >= min(values["width"], values["depth"]) - MIN_DIMENSION_MM:
        raise KernelInputError("invalid_part", "The hole must leave at least 0.005 mm of material on every side.")
    cq = cadquery()
    features = [{"id": "base-extrude", "label": "Cylinder extrusion" if kind == "cylinder" else "Rectangle extrusion", "type": "extrude"}]
    if kind == "cylinder":
        model = cq.Workplane("XY").circle(values["diameter"] / 2).extrude(values["height"])
    else:
        model = cq.Workplane("XY").box(values["width"], values["depth"], values["height"], centered=(True, True, False))
        if kind == "plate":
            # Analytical centered axis; no unstable face-index reference persists.
            cutter = cq.Workplane("XY").circle(values["hole_diameter"] / 2).extrude(values["height"])
            model = model.cut(cutter)
            features.append({"id": "center-hole", "label": "Centered through hole", "type": "cut"})
    return model.val(), kind, features


def metrics_for(shape) -> dict:
    solids = shape.Solids()
    valid = shape.isValid()
    if not valid or not solids:
        raise KernelInputError("invalid_geometry", "The kernel did not produce a valid solid body.")
    bounds = shape.BoundingBox()
    extents = [bounds.xlen, bounds.ylen, bounds.zlen]
    volume, area = shape.Volume(), shape.Area()
    center = shape.Center()
    if any(not math.isfinite(v) or v <= 0 or v > MAX_DIMENSION_MM + 1e-5 for v in extents):
        raise KernelInputError("invalid_geometry", "Solid bounds must be positive and no larger than 100000 mm per axis.")
    if not all(math.isfinite(v) for v in (volume, area, center.x, center.y, center.z)) or volume <= 0:
        raise KernelInputError("invalid_geometry", "Solid mass properties must be finite and have positive volume.")
    return {
        "volume_mm3": volume,
        "area_mm2": area,
        "bounds_mm": dict(zip(("x", "y", "z"), extents)),
        "center_mm": [center.x, center.y, center.z],
        "solid_count": len(solids),
        "face_count": len(shape.Faces()),
        "edge_count": len(shape.Edges()),
        "valid": valid,
    }


def mesh_for(shape, linear: float, angular: float) -> dict:
    from OCP.BRepMesh import BRepMesh_IncrementalMesh

    # Explicit absolute linear deflection in mm, instead of CadQuery's relative default.
    mesher = BRepMesh_IncrementalMesh(shape.wrapped, linear, False, angular, False)
    if not mesher.IsDone():
        raise KernelInputError("invalid_geometry", "Display tessellation failed.")
    vertices, triangles = shape.tessellate(linear, angular)
    if len(triangles) > MAX_MESH_TRIANGLES:
        raise KernelInputError("resource_limit", "Display mesh exceeds the experimental 200000 triangle limit.")
    if not vertices or not triangles:
        raise KernelInputError("invalid_geometry", "The solid has no display triangulation.")
    return {
        "vertices": [[v.x, v.y, v.z] for v in vertices],
        "triangles": [list(t) for t in triangles],
    }


def imported_shape(request: dict):
    encoded = request.get("data_base64")
    if not isinstance(encoded, str) or len(encoded) > ((MAX_STEP_BYTES + 2) // 3) * 4:
        raise KernelInputError("invalid_step", "STEP input must be base64 and at most 10 MiB decoded.")
    try:
        contents = base64.b64decode(encoded, validate=True)
    except (binascii.Error, ValueError):
        raise KernelInputError("invalid_step", "STEP input is not valid base64.") from None
    if not contents or len(contents) > MAX_STEP_BYTES:
        raise KernelInputError("invalid_step", "STEP input must contain between 1 byte and 10 MiB.")
    if b"ISO-10303-21" not in contents[:1024].upper():
        raise KernelInputError("invalid_step", "Expected an ISO-10303-21 STEP exchange file.")
    with tempfile.TemporaryDirectory(prefix="bcad-step-") as directory:
        path = Path(directory) / "source.step"
        path.write_bytes(contents)
        try:
            cq = cadquery()
            roots = cq.importers.importStep(str(path), unit="MM").vals()
            if not roots:
                raise ValueError("No shapes in STEP")
            shape = roots[0] if len(roots) == 1 else cq.Compound.makeCompound(roots)
        except Exception:
            raise KernelInputError("invalid_step", "OCCT could not read this STEP file.") from None
    if len(shape.Faces()) > MAX_IMPORT_FACES:
        raise KernelInputError("resource_limit", "STEP input exceeds the experimental 2000 face limit.")
    solids = shape.Solids()
    # Never discard unsupported surfaces/wires while displaying the solid subset.
    for getter in ("Faces", "Edges", "Vertices"):
        contained = {entity for solid in solids for entity in getattr(solid, getter)()}
        if set(getattr(shape, getter)()) != contained:
            raise KernelInputError("invalid_step", "Only solid STEP bodies are supported; this file also contains open surfaces, wires, or points.")
    return shape


def execute(request: dict) -> dict:
    if not isinstance(request, dict):
        raise KernelInputError("invalid_request", "Request must be an object.")
    if type(request.get("protocol")) is not int or request["protocol"] != PROTOCOL:
        raise KernelInputError("protocol_mismatch", "Expected protocol version 1.")
    if not isinstance(request.get("id"), str) or not 1 <= len(request["id"]) <= 128:
        raise KernelInputError("invalid_request", "Request id must contain 1 to 128 characters.")
    if type(request.get("revision")) is not int or not 0 <= request["revision"] <= 2**53 - 1:
        raise KernelInputError("invalid_request", "Revision must be a nonnegative safe integer.")
    op = request.get("op")
    if op == "ping":
        return {"capabilities": ["evaluate", "export_step", "export_stl", "import_step"], "kernel": kernel_metadata(), "units": "mm"}
    if op not in ("evaluate", "export_step", "export_stl", "import_step"):
        raise KernelInputError("unsupported_operation", "Unknown CAD worker operation.")
    linear, angular = tessellation_settings(request)
    has_source = "data_base64" in request
    if has_source and request.get("part") is not None:
        raise KernelInputError("invalid_request", "Choose either an exact STEP source or a primitive part, not both.")
    if op == "import_step" or (op in ("export_step", "export_stl") and has_source):
        shape, kind = imported_shape(request), "imported"
        features = [{"id": "imported-base", "label": "Imported exact STEP body (no feature history)", "type": "import"}]
    elif has_source:
        raise KernelInputError("invalid_request", "Use import_step to evaluate a STEP source.")
    else:
        shape, kind, features = build_part(request.get("part"))
    result = {"kind": kind, "metrics": metrics_for(shape), "features": features, "kernel": kernel_metadata()}
    if op in ("export_step", "export_stl"):
        suffix, mime = (".step", "model/step") if op == "export_step" else (".stl", "model/stl")
        with tempfile.TemporaryDirectory(prefix="bcad-export-") as directory:
            path = Path(directory) / ("part" + suffix)
            if op == "export_step":
                shape.exportStep(str(path), unit="MM", outputUnit="MM")
            elif not shape.exportStl(str(path), tolerance=linear, angularTolerance=angular, relative=False, parallel=False):
                raise KernelInputError("invalid_geometry", "STL export failed.")
            data = path.read_bytes()
        if len(data) > MAX_STEP_BYTES:
            raise KernelInputError("resource_limit", "Export exceeds the experimental 10 MiB output limit.")
        result.update(data_base64=base64.b64encode(data).decode("ascii"), filename=f"bcad-{kind}{suffix}", mime=mime)
    else:
        result["mesh"] = mesh_for(shape, linear, angular)
    return result


def respond(request) -> dict:
    reply = {"protocol": PROTOCOL, "id": request.get("id") if isinstance(request, dict) else None, "revision": request.get("revision") if isinstance(request, dict) else None}
    try:
        reply.update(ok=True, result=execute(request))
    except KernelInputError as error:
        reply.update(ok=False, error={"code": error.code, "message": str(error)})
    except Exception as error:
        # Native diagnostics belong to stderr; this message has no file contents or paths.
        print(f"B-CAD kernel failure: {type(error).__name__}: {error}", file=sys.stderr, flush=True)
        reply.update(ok=False, error={"code": "kernel_error", "message": "The exact CAD kernel could not complete this operation."})
    return reply


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--once", action="store_true", help="Read one request and exit.")
    options = parser.parse_args()
    # OCCT's C++ exporters write to the native stdout descriptor. Keep a dedicated
    # protocol descriptor and route both Python/native diagnostics to stderr.
    protocol_fd = os.dup(sys.stdout.fileno())
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    with os.fdopen(protocol_fd, "w", encoding="utf-8", buffering=1) as protocol_output:
        while True:
            line = sys.stdin.buffer.readline(MAX_REQUEST_BYTES + 1)
            if not line:
                break
            if len(line) > MAX_REQUEST_BYTES:
                while line and not line.endswith(b"\n"):
                    line = sys.stdin.buffer.readline(64 * 1024)
                reply = {"protocol": PROTOCOL, "id": None, "revision": None, "ok": False, "error": {"code": "resource_limit", "message": "Request exceeds 14 MiB."}}
            else:
                try:
                    request = json.loads(line, parse_constant=lambda value: (_ for _ in ()).throw(ValueError("Non-finite JSON number")))
                    reply = respond(request)
                except (ValueError, UnicodeError, RecursionError):
                    reply = {"protocol": PROTOCOL, "id": None, "revision": None, "ok": False, "error": {"code": "invalid_request", "message": "Expected a valid finite JSON request."}}
            print(json.dumps(reply, allow_nan=False, separators=(",", ":")), file=protocol_output, flush=True)
            if options.once:
                break


if __name__ == "__main__":
    main()
