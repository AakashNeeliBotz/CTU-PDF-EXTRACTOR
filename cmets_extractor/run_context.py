from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExtractionRunContext:
    """Run-scoped mutable state shared across one full extractor execution."""

    annexure_elements_cache: dict[str, dict[str, list[str]]] = field(default_factory=dict)
    cmets_element_catalog: dict[tuple[str, str], dict[str, Any]] = field(default_factory=dict)

    def reset(self) -> None:
        self.annexure_elements_cache.clear()
        self.cmets_element_catalog.clear()


def build_run_context() -> ExtractionRunContext:
    """Create a fresh extraction run context."""
    return ExtractionRunContext()


__all__ = ["ExtractionRunContext", "build_run_context"]
