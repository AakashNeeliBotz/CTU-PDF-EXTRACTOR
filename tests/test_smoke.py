from __future__ import annotations

import unittest

from tests._extractor_loader import load_extractor
from tests._helpers import REPO_ROOT

extractor = load_extractor()


class ExtractorSmokeTests(unittest.TestCase):
    def test_module_imports_and_exposes_primary_entrypoints(self) -> None:
        self.assertTrue(hasattr(extractor, "extract_all_data"))
        self.assertTrue(hasattr(extractor, "extract_34th_all_data"))
        self.assertTrue(hasattr(extractor, "extract_hybrid_meeting_data"))
        self.assertTrue(hasattr(extractor, "extract_bulk_consumers_from_pdf"))
        self.assertTrue(hasattr(extractor, "extract_margin_data"))
        self.assertTrue(hasattr(extractor, "write_to_excel"))
        self.assertTrue(hasattr(extractor, "write_bulk_consumers_to_excel"))
        self.assertTrue(hasattr(extractor, "write_margin_to_excel"))
        self.assertTrue(hasattr(extractor, "populate_element_status_sheet_from_monitoring_pdfs"))
        self.assertTrue(hasattr(extractor, "populate_element_status_sheet_from_nct_pdf"))
        self.assertTrue(hasattr(extractor, "populate_element_status_sheet_from_cmets"))
        self.assertTrue(hasattr(extractor, "save_to_csv"))

    def test_configured_primary_inputs_exist(self) -> None:
        self.assertTrue(extractor.os.path.exists(extractor.PDF_PATH))
        self.assertTrue(extractor.os.path.exists(extractor.PDF_PATH_34TH))
        self.assertTrue(extractor.os.path.exists(extractor.RE_EFFECTIVENESS_PDF_OCT))
        self.assertTrue(extractor.os.path.exists(extractor.TEMPLATE_EXCEL))

    def test_existing_output_artifacts_are_present_for_regression_baselines(self) -> None:
        self.assertTrue((REPO_ROOT / "extracted_data.csv").exists())
        self.assertTrue(
            (REPO_ROOT / "42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx").exists()
        )


if __name__ == "__main__":
    unittest.main()
