"""Retry-once import helper for Streamlit's multipage sys.modules race."""
import importlib


def resilient(module: str, name: str):
    try:
        return getattr(importlib.import_module(module), name)
    except KeyError:
        # Streamlit's script-runner can pop packages from sys.modules
        # mid-import; a retry sees a consistent state.
        return getattr(importlib.import_module(module), name)
