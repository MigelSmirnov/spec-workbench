"""Read-only engineering-obligation projection over the existing design artifacts.

Nothing here is design truth: every run rebuilds the graph from the authoring
artifacts, the deterministic assembly reports and the factory's dependency
report, derives obligations, and prints the frontier. No file is written.
"""
from __future__ import annotations

from .registry import PRECEDENCE, TYPES, ObligationType, classify
from .projection import project, focus, metrics, frontier

__all__ = ["PRECEDENCE", "TYPES", "ObligationType", "classify", "project", "focus", "metrics", "frontier"]
