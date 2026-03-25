from __future__ import annotations

import copy
import unittest

from tests._extractor_loader import load_extractor

extractor = load_extractor()


class _FakeRow(list):
    @property
    def iloc(self):
        return self

    def tolist(self):
        return list(self)


class _FakeILoc:
    def __init__(self, rows):
        self._rows = rows

    def __getitem__(self, key):
        if isinstance(key, tuple):
            row_idx, col_idx = key
            return self._rows[row_idx][col_idx]
        return _FakeRow(self._rows[key])


class _FakeTableFrame:
    def __init__(self, rows):
        self._rows = rows
        self.shape = (len(rows), len(rows[0]) if rows else 0)
        self.iloc = _FakeILoc(rows)

    def __len__(self):
        return len(self._rows)


_MISSING = object()


class _FakeCell:
    def __init__(self, worksheet, row, column):
        self._worksheet = worksheet
        self.row = row
        self.column = column

    @property
    def value(self):
        return self._worksheet._values.get((self.row, self.column))

    @value.setter
    def value(self, new_value):
        self._worksheet._values[(self.row, self.column)] = new_value
        if self.row > self._worksheet.max_row:
            self._worksheet.max_row = self.row


class _FakeWorksheet:
    def __init__(self, values=None):
        self._values = dict(values or {})
        self.max_row = max((row for row, _ in self._values), default=0)

    def cell(self, row, column, value=_MISSING):
        cell = _FakeCell(self, row, column)
        if value is not _MISSING:
            cell.value = value
        return cell


class QuantumParsingCharacterizationTests(unittest.TestCase):
    def test_reduced_quantum_defaults_to_reduced_value_for_both_fields(self) -> None:
        self.assertEqual(
            extractor.parse_34th_quantum("150 (Reduced to 50 MW)"),
            (50, 50),
        )

    def test_reduced_quantum_can_preserve_original_request_in_legacy_mode(self) -> None:
        self.assertEqual(
            extractor.parse_34th_quantum(
                "940 (reduced to 354MW)",
                preserve_original_on_reduced=True,
            ),
            (940, 354),
        )


class SubstationRuleCharacterizationTests(unittest.TestCase):
    def test_plain_ps_suffix_maps_sirohi_to_first_station(self) -> None:
        self.assertEqual(extractor.strip_ps_suffix("Sirohi PS"), "Sirohi-I")

    def test_parenthetical_hvdc_variant_prefers_specific_named_station(self) -> None:
        self.assertEqual(
            extractor.clean_substation_value("Sirohi (HVDC) PS (Sirohi-II)"),
            "Sirohi-II",
        )


class DeliberationRuleCharacterizationTests(unittest.TestCase):
    def test_scod_text_parser_prefers_last_scod_mention(self) -> None:
        text = (
            "The committee first considered SCOD as 31.12.2029 and later "
            "agreed to grant the same with SCoD of 31.03.2030."
        )
        self.assertEqual(extractor.extract_scod_date_from_text(text), "31.03.2030")

    def test_deliberation_scod_parser_prefers_last_keyword_scoped_date(self) -> None:
        app_id = "2200009999"
        deliberation_dict = {
            app_id: (
                "Application 2200009999 was discussed. The committee first agreed "
                "to grant with SCoD of 31.12.2029. Later, it agreed to grant the "
                "same with SCoD of 31.03.2030. M/s Example agreed for the same."
            )
        }
        self.assertEqual(
            extractor.extract_scod_date_from_deliberation(
                app_id,
                deliberation_dict,
                deliberation_dict[app_id],
            ),
            "31.03.2030",
        )

    def test_defer_language_wins_over_grant_language_for_status(self) -> None:
        app_id = "2200008888"
        deliberation_dict = {
            app_id: (
                "Application 2200008888 was taken up for discussion and grant, "
                "but it was decided to defer the above application to the next CMETS."
            )
        }
        self.assertEqual(
            extractor.extract_status_from_deliberation(app_id, deliberation_dict),
            "Applied",
        )

    def test_voltage_parser_uses_local_app_context(self) -> None:
        app_id = "2200001111"
        deliberation_dict = {
            app_id: (
                "2200001111 connectivity at 220 kV Barmer-I PS under App. No. 2200001111. "
                "2200002222 connectivity at 400 kV Bhadla-III PS under App. No. 2200002222."
            )
        }
        self.assertEqual(
            extractor.extract_voltage_from_deliberation(app_id, deliberation_dict),
            (220, "Barmer-I PS"),
        )


class BulkConsumerCharacterizationTests(unittest.TestCase):
    def test_detect_bulk_consumers_layout_maps_expected_columns(self) -> None:
        table_df = _FakeTableFrame(
            [
                [
                    "S. No.",
                    "Application No./Date",
                    "Name of Applicant",
                    "GNARE within Region (MW)",
                    "GNARE outside Region (MW)",
                    "Total GNARE Required (MW)",
                    "Nature of Applicant",
                    "Start Date of GNARE",
                    "End Date of GNARE",
                ],
                [
                    "1",
                    "2200007777 (01.01.2025)",
                    "M/s Example Limited",
                    "50",
                    "25",
                    "75",
                    "Captive",
                    "01.04.2026",
                    "31.03.2028",
                ],
            ]
        )

        layout = extractor._detect_bulk_consumers_layout(table_df)

        self.assertIsNotNone(layout)
        self.assertEqual(layout["app_idx"], 1)
        self.assertEqual(layout["applicant_idx"], 2)
        self.assertEqual(layout["within_idx"], 3)
        self.assertEqual(layout["outside_idx"], 4)
        self.assertEqual(layout["total_idx"], 5)
        self.assertEqual(layout["nature_idx"], 6)
        self.assertEqual(layout["start_idx"], 7)
        self.assertEqual(layout["end_idx"], 8)

    def test_bulk_consumer_substation_parser_uses_dedicated_transmission_context(self) -> None:
        text = (
            "Details of Transmission System for Grant of GNARE: "
            "A. Dedicated Transmission system for GNARE connected to "
            "intra-state transmission system at 400 kV Bikaner-IV PS."
        )

        self.assertEqual(
            extractor._extract_bulk_consumer_substation_from_text(text),
            "Bikaner-IV",
        )

    def test_bulk_consumer_status_marks_revoked_rows_explicitly(self) -> None:
        app_id = "2200007777"
        deliberation_dict = {
            app_id: (
                "Application 2200007777 was discussed and it was decided to "
                "revoke the GNARE already granted. The same shall stand revoked."
            )
        }

        self.assertEqual(
            extractor._extract_bulk_consumer_status(
                app_id,
                deliberation_dict,
                deliberation_dict[app_id],
            ),
            "Revoked",
        )


class MarginCharacterizationTests(unittest.TestCase):
    def test_margin_pooling_station_prefers_text_after_complex_marker(self) -> None:
        self.assertEqual(
            extractor.extract_margin_pooling_ss("Bhadla Complex (Bhadla-II)"),
            "Bhadla-II",
        )

    def test_margin_parent_state_propagation_uses_most_common_child_state(self) -> None:
        records = [
            {"sl_no": "12", "state": None},
            {"sl_no": "12A", "state": "Rajasthan"},
            {"sl_no": "12B", "state": "Rajasthan"},
            {"sl_no": "12C", "state": "Gujarat"},
        ]

        result = extractor.propagate_state_to_parent_complex(copy.deepcopy(records))

        self.assertEqual(result[0]["state"], "Rajasthan")


class ElementStatusCharacterizationTests(unittest.TestCase):
    def test_annexure_parser_accepts_number_on_separate_line(self) -> None:
        block_text = (
            "Annexure-II\n"
            "1.\n"
            "765 kV D/c line from A to B\n"
            "2. 400 kV ICT at X"
        )

        self.assertEqual(
            extractor.parse_annexure_elements_from_block(block_text),
            [
                "765 kV D/c line from A to B",
                "400 kV ICT at X",
            ],
        )

    def test_element_code_generation_ignores_optional_line_tail(self) -> None:
        base_scope = "765 kV D/c line from A to B"
        augmented_scope = (
            "765 kV D/c line from A to B along with 1x125 MVAr bus reactor"
        )

        self.assertEqual(
            extractor.es_generate_unique_code(base_scope),
            extractor.es_generate_unique_code(augmented_scope),
        )

    def test_nct_length_applies_double_circuit_multiplier(self) -> None:
        self.assertEqual(
            extractor.es_calculate_nct_length(
                "765 kV D/c line from A to B",
                "100 km",
            ),
            200,
        )

    def test_scheme_detail_parser_keeps_region_phase_and_part(self) -> None:
        self.assertEqual(
            extractor.es_extract_scheme_details(
                "Transmission system for evacuation from Rajasthan REZ Phase-IV (Part-2) SPV: Test"
            ),
            ("Rajasthan REZ Phase-IV", "Rajasthan REZ Phase-IV (Part-2)"),
        )

    def test_element_status_sheet_population_preserves_existing_row_without_overwrite(self) -> None:
        ws = _FakeWorksheet(
            {
                (4, 2): "EL-AAAAA",
                (4, 5): "765 kV D/c line from A to B",
                (4, 9): "OLDMODE",
            }
        )
        src_cols = {
            "Scope": "Scope",
            "ElementCode": "ElementCode",
            "Mode": "Mode",
        }

        stats = extractor.es_populate_sheet_from_source_rows(
            ws,
            [
                {
                    "Scope": "765 kV D/c line from A to B",
                    "ElementCode": "EL-AAAAA",
                    "Mode": "TBCB",
                },
                {
                    "Scope": "400 kV ICT at X",
                    "ElementCode": "EL-BBBBB",
                    "Mode": "RTM",
                },
            ],
            src_cols,
            source_label="TBCB",
        )

        self.assertEqual(stats["updated_rows"], 1)
        self.assertEqual(stats["appended_rows"], 1)
        self.assertEqual(ws.cell(4, 9).value, "OLDMODE")
        self.assertEqual(ws.cell(5, 2).value, "EL-BBBBB")
        self.assertEqual(ws.cell(5, 5).value, "400 kV ICT at X")
        self.assertEqual(ws.cell(5, 9).value, "RTM")

    def test_cmets_catalog_append_keeps_cmets_columns_blank_for_new_rows(self) -> None:
        ws = _FakeWorksheet(
            {
                (4, 2): "EL-AAAAA",
                (4, 5): "765 kV D/c line from A to B",
            }
        )
        catalog = {
            ("scope-a", "EL-AAAAA"): {
                "scope": "765 kV D/c line from A to B",
                "code": "EL-AAAAA",
                "categories": {"ATS"},
                "meetings": {"42"},
            },
            ("scope-b", "EL-BBBBB"): {
                "scope": "400 kV ICT at X",
                "code": "EL-BBBBB",
                "categories": {"CTS"},
                "meetings": {"35", "34"},
            },
        }

        stats = extractor.es_append_cmets_catalog_entries(ws, catalog)

        self.assertEqual(stats["updated_rows"], 1)
        self.assertEqual(stats["appended_rows"], 1)
        self.assertEqual(ws.cell(4, 30).value, "CMETS meeting(s): 42")
        self.assertEqual(ws.cell(5, 2).value, "EL-BBBBB")
        self.assertEqual(ws.cell(5, 5).value, "400 kV ICT at X")
        self.assertIsNone(ws.cell(5, 3).value)
        self.assertIsNone(ws.cell(5, 4).value)
        self.assertIsNone(ws.cell(5, 8).value)
        self.assertIsNone(ws.cell(5, 9).value)
        self.assertEqual(ws.cell(5, 30).value, "CMETS meeting(s): 34, 35")


class HybridContextCharacterizationTests(unittest.TestCase):
    def test_scope_text_to_app_ignores_immediate_self_row_match_and_stops_before_next_row(self) -> None:
        text = (
            "10. 2200001396 Applicant A was discussed and decided to defer the above application "
            "to the next CMETS meeting. 11. 2200001397 Applicant B was granted connectivity."
        )

        scoped = extractor.scope_text_to_app(text, "2200001396")

        self.assertIn("2200001396", scoped)
        self.assertIn("defer the above application", scoped)
        self.assertNotIn("2200001397", scoped)

    def test_resolve_hybrid_status_prefers_direct_exact_applied_context_over_shared_grant(self) -> None:
        app_id = "2200002125"
        exact_text = (
            "10. 2200002125 Applicant A requested connectivity and it was decided to defer "
            "the above application for discussion in next CMETS."
        )
        inferred_text = (
            "2200002123 and 2200002125 were proposed to grant connectivity at Fatehgarh-IV PS "
            "with details of transmission system under applicant scope."
        )

        status = extractor.resolve_hybrid_status(
            None,
            exact_text=exact_text,
            inferred_text=inferred_text,
            app_id=app_id,
        )

        self.assertEqual(status, "Applied")


class ReEffectivenessCharacterizationTests(unittest.TestCase):
    def test_42nd_rule_keeps_granted_equal_to_applied_even_for_withdrawn_rows(self) -> None:
        records = [
            {
                "application_id_enhancement_5_2_or_revision": "2200002125",
                "application_quantum_mw": 150,
                "status_of_application": "Withdrawn",
                "cmets_gna_approved": 42,
            }
        ]

        result = extractor.apply_re_effectiveness_rules_42nd(
            copy.deepcopy(records),
            lookup={},
        )

        self.assertEqual(result[0]["granted_quantum_mw"], 150)

    def test_hybrid_reg52_expansion_keeps_first_row_full_and_later_rows_partial(self) -> None:
        records = [
            {
                "application_id_enhancement_5_2_or_revision": "2200002125",
                "lta_application_id": "412100010",
                "gna_st_ii_application_id": None,
                "cmets_gna_approved": 42,
                "cmets_gna_meeting_date": "11.11.2025",
                "name_of_developers": "Juniper Green Stellar Private Limited",
                "state": "Rajasthan",
                "region": "NR",
                "application_quantum_mw": 150,
                "status_of_application": "Granted",
                "substation": "Fatehgarh-IV",
                "voltage_level_kv": 220,
            }
        ]
        lookup = {
            "412100010": {
                "project_type": "Solar",
                "connectivity_mw": 150,
                "solar_mw": 150,
                "wind_mw": None,
                "bess_mw": None,
                "effective_date": "30.04.2026",
                "stii_ids": ["1200003827", "1200003910"],
            }
        }

        result = extractor.apply_re_effectiveness_rules_42nd(
            copy.deepcopy(records),
            lookup=lookup,
        )

        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["gna_st_ii_application_id"], "1200003827")
        self.assertEqual(result[0]["application_quantum_mw"], 150)
        self.assertNotIn("_partial_row", result[0])

        self.assertEqual(result[1]["gna_st_ii_application_id"], "1200003910")
        self.assertTrue(result[1]["_partial_row"])
        self.assertEqual(result[1]["status_of_application"], "Granted")
        self.assertEqual(result[1]["voltage_level_kv"], 220)
        self.assertNotIn("application_quantum_mw", result[1])
        self.assertNotIn("cmets_gna_meeting_date", result[1])


class OutputPreparationCharacterizationTests(unittest.TestCase):
    def test_fill_empty_granted_quantum_zeros_42nd_and_withdrawn_rows_only(self) -> None:
        records = [
            {
                "gna_st_ii_application_id": "2200000793",
                "cmets_gna_approved": 34,
                "status_of_application": "Withdrawn",
                "granted_quantum_mw": None,
            },
            {
                "application_id_enhancement_5_2_or_revision": "2200001678",
                "cmets_gna_approved": 38,
                "status_of_application": "Applied",
                "granted_quantum_mw": None,
            },
            {
                "gna_st_ii_application_id": "1200003910",
                "_partial_row": True,
                "granted_quantum_mw": None,
            },
        ]

        result = extractor.fill_empty_granted_quantum(copy.deepcopy(records))

        self.assertEqual(result[0]["granted_quantum_mw"], 0)
        self.assertIsNone(result[1]["granted_quantum_mw"])
        self.assertIsNone(result[2]["granted_quantum_mw"])

    def test_data_capture_excel_value_preserves_numeric_and_date_types(self) -> None:
        self.assertEqual(
            extractor.prepare_data_capture_excel_value("application_quantum_mw", "150.0"),
            150,
        )
        parsed = extractor.prepare_data_capture_excel_value(
            "gna_operationalization_date",
            "31.03.2030",
        )
        self.assertEqual(parsed.strftime("%d.%m.%Y"), "31.03.2030")


if __name__ == "__main__":
    unittest.main()
