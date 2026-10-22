"""Small dimensional expression language; never evaluates Python code."""
import ast
import math
import re
from dataclasses import dataclass


class ExpressionError(ValueError):
    pass


@dataclass(frozen=True)
class Quantity:
    value: float
    dimension: int = 0  # exponent of length; this first slice accepts lengths only


UNITS = {"mm": 1.0, "cm": 10.0, "m": 1000.0, "in": 25.4, "inch": 25.4,
         "ft": 304.8, "um": 0.001}
_UNIT_LITERAL = re.compile(r"(?<![\w.])(\d+(?:\.\d*)?|\.\d+)([eE][+-]?\d+)?\s*(mm|cm|inch|in|ft|um|m)\b")
_PAREN_UNIT = re.compile(r"\)\s*(mm|cm|inch|in|ft|um|m)\b")


def normalize_units(source):
    # A quantity suffix binds to its literal before division/multiplication.
    # Without parentheses, `2 in / 4 in` becomes length squared after rewriting.
    source = _UNIT_LITERAL.sub(lambda match: "(" + match.group(1) + (match.group(2) or "") + " * unit_" + match.group(3) + ")", source)
    while match := _PAREN_UNIT.search(source):
        start, depth = match.start(), 1
        while start > 0 and depth:
            start -= 1
            if source[start] == ")":
                depth += 1
            elif source[start] == "(":
                depth -= 1
        if depth:
            break  # the AST parser reports the unmatched parenthesis
        source = source[:start] + "(" + source[start:match.start() + 1] + " * unit_" + match.group(1) + ")" + source[match.end():]
    return source


def evaluate_parameters(expressions):
    """Resolve named length expressions to mm, detecting cycles and dimensions.

    Bare final numbers are millimetres. In arithmetic, bare numbers are scalars:
    ``width / 2`` works, and ``width + 2 mm`` is explicit and unambiguous.
    """
    resolved, visiting = {}, set()

    def resolve(name):
        if name in resolved:
            return resolved[name]
        if name not in expressions:
            raise ExpressionError(f"Unknown parameter: {name}")
        if name in visiting:
            raise ExpressionError(f"Cyclic parameter reference: {name}")
        visiting.add(name)
        source = expressions[name]
        if not isinstance(source, str) or not 0 < len(source) <= 256:
            raise ExpressionError(f"{name}: use an expression of 1–256 characters")
        # 'in' is a Python keyword; replace all supported suffixes before parsing.
        source = normalize_units(source)
        try:
            tree = ast.parse(source.strip(), mode="eval")
            if sum(1 for _ in ast.walk(tree)) > 100:
                raise ExpressionError("Expression is too complex")
            result = walk(tree.body, 0)
        except (SyntaxError, ZeroDivisionError, OverflowError, RecursionError) as exc:
            raise ExpressionError(f"{name}: invalid expression") from exc
        if result.dimension not in (0, 1):
            raise ExpressionError(f"{name}: expression must be a length")
        if not math.isfinite(result.value) or not 0.01 <= result.value <= 100000:
            raise ExpressionError(f"{name}: length must be between 0.01 and 100000 mm")
        resolved[name] = Quantity(result.value, 1)
        visiting.remove(name)
        return resolved[name]

    def walk(node, depth):
        if depth > 24:
            raise ExpressionError("Expression is too deeply nested")
        if isinstance(node, ast.Constant) and type(node.value) in (int, float):
            if not math.isfinite(node.value) or abs(node.value) > 1e12:
                raise ExpressionError("Number is out of range")
            return Quantity(float(node.value))
        if isinstance(node, ast.Name):
            if node.id.startswith("unit_") and node.id[5:] in UNITS:
                return Quantity(UNITS[node.id[5:]], 1)
            if node.id == "pi":
                return Quantity(math.pi)
            return resolve(node.id)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            q = walk(node.operand, depth + 1)
            return Quantity(q.value * (-1 if isinstance(node.op, ast.USub) else 1), q.dimension)
        if isinstance(node, ast.BinOp):
            a, b = walk(node.left, depth + 1), walk(node.right, depth + 1)
            if isinstance(node.op, (ast.Add, ast.Sub)):
                if a.dimension != b.dimension:
                    raise ExpressionError("Cannot add a scalar and a length; include mm")
                return Quantity(a.value + b.value * (-1 if isinstance(node.op, ast.Sub) else 1), a.dimension)
            if isinstance(node.op, ast.Mult):
                return Quantity(a.value * b.value, a.dimension + b.dimension)
            if isinstance(node.op, ast.Div):
                return Quantity(a.value / b.value, a.dimension - b.dimension)
        raise ExpressionError("Use numbers, length units, parameter names and + − * / only")

    return {name: resolve(name).value for name in expressions}
