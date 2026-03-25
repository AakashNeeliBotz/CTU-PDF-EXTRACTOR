from __future__ import annotations

import importlib
import unittest

from tests._extractor_loader import _install_stub_modules
from tests._helpers import ensure_repo_root_on_path


_install_stub_modules()
ensure_repo_root_on_path()


class ArchitectureSmokeTests(unittest.TestCase):
    def test_pipeline_and_run_context_modules_import(self) -> None:
        pipeline = importlib.import_module("cmets_extractor.pipeline")
        run_context = importlib.import_module("cmets_extractor.run_context")

        self.assertTrue(hasattr(pipeline, "run_pipeline"))
        self.assertTrue(hasattr(pipeline, "PipelineRunResult"))
        self.assertTrue(hasattr(run_context, "ExtractionRunContext"))
        self.assertTrue(hasattr(run_context, "build_run_context"))

    def test_meeting_modules_expose_extracted_entrypoints(self) -> None:
        forty_second = importlib.import_module("cmets_extractor.domain.meetings.forty_second")
        hybrid = importlib.import_module("cmets_extractor.domain.meetings.hybrid")
        thirty_fourth = importlib.import_module("cmets_extractor.domain.meetings.thirty_fourth")

        self.assertTrue(hasattr(forty_second, "extract_all_data"))
        self.assertTrue(hasattr(hybrid, "extract_hybrid_meeting_data"))
        self.assertTrue(hasattr(thirty_fourth, "extract_34th_all_data"))


if __name__ == "__main__":
    unittest.main()
