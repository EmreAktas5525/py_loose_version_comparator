"""Loose version comparison for strings that follow no strict specification.

See :mod:`py_loose_version_comparator.core` for the implementation.
"""

from .core import (
    LooseVersion,
    compare_versions,
    parse_version,
    sort_versions,
)

__all__ = [
    "LooseVersion",
    "compare_versions",
    "parse_version",
    "sort_versions",
]

__version__ = "1.0.0"
