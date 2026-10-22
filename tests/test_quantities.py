"""Dimensional arithmetic and restricted expression behavior."""

import unittest

from bcad.quantities import ExpressionError, evaluate_parameters


class QuantityExpressionTests(unittest.TestCase):
    def test_named_lengths_mixed_units_and_scientific_notation(self):
        result = evaluate_parameters({"width": "2 in + 1 cm", "depth": "width / 2", "height": "8e-3 m"})
        self.assertAlmostEqual(result["width"], 60.8)
        self.assertAlmostEqual(result["depth"], 30.4)
        self.assertAlmostEqual(result["height"], 8)

    def test_unit_literals_are_atomic_in_products_and_division(self):
        result = evaluate_parameters({"width": "2 in / 4 in * 12 mm", "depth": "(2 + 3) cm", "height": "(1 + (2 + 3)) mm"})
        self.assertAlmostEqual(result["width"], 6)
        self.assertAlmostEqual(result["depth"], 50)
        self.assertAlmostEqual(result["height"], 6)
        with self.assertRaises(ExpressionError):
            evaluate_parameters({"width": "1 / 2 mm"})

    def test_cycles_unknown_names_and_inconsistent_dimensions_are_diagnostics(self):
        cases = [
            {"width": "depth", "depth": "width"},
            {"width": "missing + 1 mm"},
            {"width": "2 mm + 3"},
            {"width": "2 mm * 3 mm"},
            {"width": "1 / 0"},
        ]
        for expressions in cases:
            with self.subTest(expressions=expressions), self.assertRaises(ExpressionError):
                evaluate_parameters(expressions)

    def test_python_execution_and_non_numeric_constructs_are_rejected(self):
        malicious = [
            "__import__('os').getcwd()", "open('anything').read()", "(1).__class__",
            "[1,2][0]", "[x for x in (1,2)]", "lambda: 1", "True", "'8 mm'",
            "2 ** 999999999", "float('nan')", "1e999", "(1,2)", "{'width': 1}",
        ]
        for expression in malicious:
            with self.subTest(expression=expression), self.assertRaises(ExpressionError):
                evaluate_parameters({"width": expression})


if __name__ == "__main__":
    unittest.main()
