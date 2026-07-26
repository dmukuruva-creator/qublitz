"""Guard against sub-Hz false-precision number formats (P0.2).

Asserts no page uses 9-decimal display formats (``%.9f`` / ``:.9f``), which
render values like ``4.027000000 GHz`` — nine decimals of GHz is sub-Hz
precision for a quantity assigned at MHz-ish precision.
"""
import glob
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_no_nine_decimal_formats():
    offenders = []
    for path in glob.glob(os.path.join(ROOT, "pages", "*.py")):
        with open(path, encoding="utf-8") as f:
            text = f.read()
        if "%.9f" in text or ":.9f" in text:
            offenders.append(os.path.relpath(path, ROOT))
    assert not offenders, f"9-decimal display format found in: {offenders}"
