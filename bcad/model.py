"""Version 1 experimental documents and atomic, bounded undo transactions."""
import base64
import copy
import json
import uuid

from .quantities import ExpressionError, evaluate_parameters

DEFAULTS = {
    "box": {"width": "80 mm", "depth": "50 mm", "height": "8 mm"},
    "plate": {"width": "80 mm", "depth": "50 mm", "height": "8 mm", "hole_diameter": "12 mm"},
    "cylinder": {"diameter": "40 mm", "height": "20 mm"},
}
MAX_STEP = 10 * 1024 * 1024
MAX_DOCUMENT = 15 * 1024 * 1024


class DocumentError(ValueError):
    pass


def new_document(kind="plate"):
    if not isinstance(kind, str) or kind not in DEFAULTS:
        raise DocumentError("Choose box, plate or cylinder")
    return {"format": "bcad", "schema_version": 1, "document_id": str(uuid.uuid4()),
            "name": "Untitled part", "revision": 0,
            "units": {"length": "mm", "angle": "deg"},
            "part": {"kind": kind, "parameters": DEFAULTS[kind].copy()}}


def decode_step(data):
    if not isinstance(data, str) or len(data) > ((MAX_STEP + 2) // 3) * 4:
        raise DocumentError("STEP import limit is 10 MiB")
    try:
        decoded = base64.b64decode(data, validate=True)
    except ValueError as exc:
        raise DocumentError("Invalid STEP encoding") from exc
    if not decoded or len(decoded) > MAX_STEP:
        raise DocumentError("STEP file is empty or exceeds 10 MiB")
    return decoded


def validate_document(document):
    if not isinstance(document, dict) or set(document) != {"format", "schema_version", "document_id", "name", "revision", "units", "part"}:
        raise DocumentError("Unrecognized document fields")
    if document["format"] != "bcad" or type(document["schema_version"]) is not int or document["schema_version"] != 1:
        raise DocumentError("Unsupported document version")
    try:
        uuid.UUID(document["document_id"])
    except (ValueError, TypeError, AttributeError) as exc:
        raise DocumentError("Invalid document ID") from exc
    if not isinstance(document["name"], str) or not 1 <= len(document["name"]) <= 120:
        raise DocumentError("Document name must be 1–120 characters")
    if type(document["revision"]) is not int or not 0 <= document["revision"] < 2**31:
        raise DocumentError("Invalid document revision")
    if document["units"] != {"length": "mm", "angle": "deg"}:
        raise DocumentError("Version 1 uses mm and degrees")
    part = document["part"]
    if not isinstance(part, dict):
        raise DocumentError("Invalid part")
    kind = part.get("kind")
    if kind == "imported":
        if set(part) != {"kind", "parameters", "source"} or part["parameters"] != {}:
            raise DocumentError("Imported parts have no editable parameters")
        source = part["source"]
        if not isinstance(source, dict) or set(source) != {"format", "data_base64"} or source["format"] != "step":
            raise DocumentError("Imported parts must embed their STEP source")
        decode_step(source["data_base64"])
        return None
    if not isinstance(kind, str) or kind not in DEFAULTS or set(part) != {"kind", "parameters"}:
        raise DocumentError("Unsupported part kind")
    parameters = part["parameters"]
    if not isinstance(parameters, dict) or set(parameters) != set(DEFAULTS[kind]):
        raise DocumentError("Unexpected or missing parameters")
    try:
        values = evaluate_parameters(parameters)
    except ExpressionError as exc:
        raise DocumentError(str(exc)) from exc
    if kind == "plate" and values["hole_diameter"] >= min(values["width"], values["depth"]):
        raise DocumentError("Hole diameter must be smaller than width and depth")
    return values


class Controller:
    def __init__(self, core):
        self.core, self.document, self.result = core, new_document(), None
        self.undo_stack, self.redo_stack = [], []
        self.error = None
        try:
            self.result = self.evaluate(self.document)
        except RuntimeError as exc:
            self.error = str(exc)

    def evaluate(self, document, op="evaluate"):
        values = validate_document(document)
        if values is None:
            return self.core.request("import_step" if op == "evaluate" else op,
                                     data_base64=document["part"]["source"]["data_base64"],
                                     revision=document["revision"])
        return self.core.request(op, part={"kind": document["part"]["kind"], "values": values},
                                 revision=document["revision"])

    def state(self, document=None, result=None, preview=False):
        return {"document": copy.deepcopy(document or self.document),
                "result": result if result is not None else self.result,
                "history": {"can_undo": bool(self.undo_stack), "can_redo": bool(self.redo_stack)},
                "kernel_available": self.result is not None, "error": self.error, "preview": preview}

    def candidate(self, payload):
        kind = payload.get("kind")
        candidate = copy.deepcopy(self.document)
        candidate["part"] = {"kind": kind, "parameters": payload.get("parameters")}
        candidate["revision"] += 1
        if "name" in payload:
            candidate["name"] = payload["name"]
        return candidate

    def apply(self, candidate, preview=False, reset=False):
        result = self.evaluate(candidate)  # failures cannot modify document or history
        if preview:
            return self.state(candidate, result, True)
        if reset:
            self.undo_stack.clear()
        else:
            self.undo_stack.append((self.document, self.result))
            self.undo_stack = self.undo_stack[-20:]
        self.redo_stack.clear()
        self.document, self.result, self.error = copy.deepcopy(candidate), result, None
        return self.state()

    def history(self, redo=False):
        source, target = (self.redo_stack, self.undo_stack) if redo else (self.undo_stack, self.redo_stack)
        if not source:
            raise DocumentError("No further history")
        document, result = source.pop()
        target.append((self.document, self.result))
        # Revisions identify events, including undo, rather than an old history slot.
        document = copy.deepcopy(document)
        document["revision"] = self.document["revision"] + 1
        self.document, self.result = document, result
        return self.state()

    def export(self, format):
        if format not in ("step", "stl"):
            raise DocumentError("Choose STEP or STL")
        return self.evaluate(self.document, "export_" + format)

    def import_step(self, payload):
        decode_step(payload.get("data_base64"))
        candidate = new_document()
        candidate["name"] = str(payload.get("filename") or "Imported STEP")[:120]
        candidate["revision"] = self.document["revision"] + 1
        candidate["part"] = {"kind": "imported", "parameters": {},
                             "source": {"format": "step", "data_base64": payload["data_base64"]}}
        return self.apply(candidate)


def parse_document(text):
    if len(text.encode("utf-8")) > MAX_DOCUMENT:
        raise DocumentError("Document exceeds 15 MiB")
    try:
        document = json.loads(text)
    except (ValueError, RecursionError) as exc:
        raise DocumentError("Invalid document JSON") from exc
    validate_document(document)
    return document
