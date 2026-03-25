from __future__ import annotations

import unittest

from tests._helpers import REPO_ROOT, find_first_row, find_rows, load_csv_rows


class OutputRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.rows = load_csv_rows(REPO_ROOT / "extracted_data.csv")

    def test_validated_34th_ids_exist_in_baseline_csv(self) -> None:
        self.assertTrue(
            find_rows(self.rows, gna_st_ii_application_id="2200000793"),
            "Expected 2200000793 in baseline extracted_data.csv",
        )
        self.assertTrue(
            find_rows(self.rows, gna_st_ii_application_id="2200000891"),
            "Expected 2200000891 in baseline extracted_data.csv",
        )

    def test_sirohi_hvdc_normalization_is_present_in_baseline_output(self) -> None:
        row = find_first_row(self.rows, gna_st_ii_application_id="2200000827")
        self.assertEqual(row["substation"], "Sirohi-II")

    def test_reduced_quantum_row_keeps_50mw_values_in_baseline_output(self) -> None:
        row = find_first_row(self.rows, gna_st_ii_application_id="2200001044")
        self.assertEqual(float(row["application_quantum_mw"]), 50.0)
        self.assertEqual(float(row["granted_quantum_mw"]), 50.0)
        self.assertEqual(float(row["installed_breakup_solar_mw"]), 50.0)

    def test_lta_expansion_partial_rows_keep_later_columns_blank_in_baseline_output(self) -> None:
        partial_rows = find_rows(self.rows, lta_application_id="412100010", _partial_row="True")
        self.assertTrue(partial_rows, "Expected partial LTA expansion rows for 412100010")
        sample = partial_rows[0]
        self.assertEqual(sample["status_of_application"], "Granted")
        self.assertEqual(sample["voltage_level_kv"], "220.0")
        self.assertEqual(sample["application_quantum_mw"], "")
        self.assertEqual(sample["type"], "")
        self.assertEqual(sample["granted_quantum_mw"], "")


if __name__ == "__main__":
    unittest.main()
