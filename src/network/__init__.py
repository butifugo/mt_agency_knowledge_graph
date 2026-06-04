"""Network package initialization"""

# Backwards-compatibility for graph pickles built before the `src/` layout, when this
# package was importable as top-level `network`. The exports in
# `src/network/exports/*.pkl` reference `network.schema` for their dataclasses, so we
# alias the old module paths to the current ones to let `pickle.load` resolve them.
import sys as _sys

from . import schema as _schema

_sys.modules.setdefault("network", _sys.modules[__name__])
_sys.modules.setdefault("network.schema", _schema)