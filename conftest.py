"""Pytest path setup: the repository root carries both the harness and the
vendored aeros runtime surface, so tests run from a plain checkout. Set
AEROS_SRC to point at a full AEROS runtime checkout to test against it instead."""

import os
import sys

HARNESS_ROOT = os.path.dirname(__file__)
_paths = [HARNESS_ROOT]
_override = os.environ.get("AEROS_SRC")
if _override:
    _paths.insert(0, _override)
for path in _paths:
    if path not in sys.path:
        sys.path.insert(0, path)
