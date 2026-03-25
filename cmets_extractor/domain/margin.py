from __future__ import annotations

import os
import re

import camelot
import pandas as pd

from cmets_extractor.config import MARGIN_PDF_DIR, STATE_NAME_MAP


def normalize_state_name(state_value, *, normalize_substation_fn=None):
    """Normalize state name to the legacy Margin-sheet full-name output."""
    if not state_value or pd.isna(state_value):
        return None

    state_str = str(state_value).strip()
    for key, normalized in STATE_NAME_MAP.items():
        if state_str.upper() == key.upper():
            return normalized

    if normalize_substation_fn is not None:
        return normalize_substation_fn(state_str)
    return state_str.title()


def extract_additional_info_from_pooling_ss(pooling_ss_value):
    """Split legacy Margin-sheet pooling station text into station and extra info."""
    if not pooling_ss_value or not isinstance(pooling_ss_value, str):
        return (pooling_ss_value, None)

    station_name = pooling_ss_value.strip()
    additional_info = None

    parentheses_pattern = r"\s*\(([^)]+)\)\s*$"
    match = re.search(parentheses_pattern, station_name)
    if not match:
        incomplete_paren_pattern = r"\s*\(([^)]+)\s*$"
        match = re.search(incomplete_paren_pattern, station_name)

    if match:
        content = match.group(1).strip()
        if content:
            additional_info = content
            station_name = station_name[:match.start()].strip()

    if not additional_info:
        info_keywords = [
            r"\s+Section\s+linked\s+to",
            r"\s+section\s+linked\s+to",
            r"\s+linked\s+to",
            r"\s+expansion\s+",
            r"\s+with\s+expansion",
            r"\s+including\s+",
        ]
        for keyword in info_keywords:
            match = re.search(keyword, station_name, re.IGNORECASE)
            if match:
                split_pos = match.start()
                additional_info = station_name[split_pos:].strip()
                station_name = station_name[:split_pos].strip()
                break

    station_name = station_name.strip("- \t\n")
    if additional_info and not additional_info.strip():
        additional_info = None

    return (station_name, additional_info)


def clean_margin_substation_name(substation_value):
    """Apply the legacy Margin-sheet station cleanup rules verbatim."""
    if not substation_value or not isinstance(substation_value, str):
        return substation_value

    cleaned = substation_value.strip()
    coord_pattern = r'\d+°\d+[\'′]\d+[\"″]?[NS]?\s*\d*°?\d*[\'′]?\d*[\"″]?[EW]?'
    cleaned = re.sub(coord_pattern, "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^\d+(?:/\d+)*\s*k[Vv]\s*", "", cleaned)
    cleaned = re.sub(r"\s+\d+(?:/\d+)*(?:\s*k[Vv])?\s*$", "", cleaned)
    cleaned = re.sub(r"\s*\[[^\]]+\]", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*\([^)]*\)", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:GIS|AIS)(?:\s*-?\s*[IVX]+)?\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:PS|P\.S\.)\s*(-\s*[IVX\d]+)", r"\1", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s*(?:PS|P\.S\.|S/[sS]|S/S)\s*$", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"\s+(?:PS|P\.S\.)\s+", " ", cleaned, flags=re.IGNORECASE)
    cleaned = cleaned.rstrip("#*~+ ")
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


def replace_multiplication_patterns(text):
    """Apply the legacy Margin-sheet Expected CoD multiplication replacement."""
    if not text or not isinstance(text, str):
        return text

    pattern = r"(\d+)\s*[xX×]\s*(\d+(?:\.\d+)?)"

    def replace_match(match):
        count = float(match.group(1))
        capacity = float(match.group(2))
        result = count * capacity
        if result == int(result):
            return str(int(result))
        return str(result)

    return re.sub(pattern, replace_match, text)


def propagate_state_to_parent_complex(records):
    """Preserve the legacy Margin-sheet parent-state propagation logic."""
    if not records:
        return records

    parent_map = {}
    parent_records = {}

    for record in records:
        sl_no = record.get("sl_no", "")
        if not sl_no:
            continue

        sl_no_str = str(sl_no).strip()
        if sl_no_str.isdigit():
            parent_records[sl_no_str] = record
            if sl_no_str not in parent_map:
                parent_map[sl_no_str] = []
        elif len(sl_no_str) > 1 and sl_no_str[0].isdigit():
            parent_num = ""
            for char in sl_no_str:
                if char.isdigit():
                    parent_num += char
                else:
                    break

            if parent_num:
                if parent_num not in parent_map:
                    parent_map[parent_num] = []
                parent_map[parent_num].append(record)

    propagation_count = 0
    for parent_num, sub_rows in parent_map.items():
        if parent_num not in parent_records:
            continue

        parent_record = parent_records[parent_num]
        parent_state = parent_record.get("state")
        if not parent_state or str(parent_state).strip() in ["", "nan", "None"]:
            sub_states = []
            for sub_row in sub_rows:
                sub_state = sub_row.get("state")
                if sub_state and str(sub_state).strip() not in ["", "nan", "None"]:
                    sub_states.append(str(sub_state).strip())

            if sub_states:
                from collections import Counter

                most_common_state = Counter(sub_states).most_common(1)[0][0]
                parent_record["state"] = most_common_state
                propagation_count += 1
                print(
                    f"      [State Propagation] sl_no={parent_num}: "
                    f"Set state to '{most_common_state}' from sub-rows"
                )

    if propagation_count > 0:
        print(
            "      [State Propagation] Total: "
            f"{propagation_count} parent complex rows updated with states from sub-rows"
        )
    return records


def extract_margin_pooling_ss(raw_value):
    """Extract text after 'Complex' when present, matching the legacy Margin logic."""
    if not raw_value:
        return raw_value

    if "Complex" in raw_value:
        idx = raw_value.find("Complex")
        after_complex = raw_value[idx + 7 :].strip()
        if after_complex:
            cleaned = after_complex.lstrip("(\n \t")
            if cleaned.startswith(")"):
                cleaned = cleaned[1:].strip()
            if cleaned.endswith(")"):
                cleaned = cleaned.rstrip(")")
            if cleaned:
                return cleaned
    return raw_value


def _to_margin_numeric(value):
    if pd.isna(value):
        return None
    value_str = str(value).strip()
    if value_str in ["", "nan", "None"]:
        return None
    try:
        cleaned = value_str.replace(",", "")
        return float(cleaned)
    except Exception:
        return value_str


def extract_margin_records_from_table(
    data_df,
    current_region=None,
    current_timeline=None,
    parent_sl_no=None,
    custom_serial_counter=0,
    *,
    normalize_state_name_fn=None,
):
    """Extract one legacy Margin table while persisting context across continuations."""
    margin_records = []
    if normalize_state_name_fn is None:
        normalize_state_name_fn = normalize_state_name

    for _, row in data_df.iterrows():
        sl_no_val = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
        raw_pooling_ss = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
        pooling_ss_val = extract_margin_pooling_ss(raw_pooling_ss)

        if sl_no_val and "\n" in sl_no_val:
            parts = sl_no_val.split("\n", 1)
            if len(parts) == 2:
                potential_sl_no = parts[0].strip()
                station_name = parts[1].strip()
                if not pooling_ss_val and station_name:
                    pooling_ss_val = station_name
                    sl_no_val = potential_sl_no if potential_sl_no else ""
                    print(
                        f"      [Split sl_no] '{parts[0]}\\n{parts[1]}' -> "
                        f"sl_no='{sl_no_val}', pooling_ss='{pooling_ss_val}'"
                    )

        sl_no_lower = sl_no_val.lower()
        pooling_ss_lower = pooling_ss_val.lower()
        combined_text = f"{sl_no_val} {pooling_ss_val}".lower()

        if "northern region" in combined_text:
            current_region = "NR"
            continue
        if "southern region" in combined_text:
            current_region = "SR"
            continue
        if "western region" in combined_text:
            current_region = "WR"
            continue
        if "north eastern region" in combined_text or "northeastern region" in combined_text:
            current_region = "NER"
            continue

        if "existing re pooling station" in combined_text or "existing ps" in combined_text:
            current_timeline = "Existing"
            continue
        if "commissioning between" in combined_text or "commissioning by" in combined_text:
            timeline_text = sl_no_val if "commissioning" in sl_no_lower else pooling_ss_val
            if timeline_text and len(timeline_text) > 2 and timeline_text[1] == ".":
                timeline_text = timeline_text[3:].strip()
            if "between" in timeline_text.lower():
                find_idx = timeline_text.lower().find("between")
                if find_idx != -1:
                    date_part = timeline_text[find_idx + 7 :].strip()
                    current_timeline = f"Between {date_part}"
            elif "by" in timeline_text.lower():
                find_idx = timeline_text.lower().find("by")
                if find_idx != -1:
                    date_part = timeline_text[find_idx + 2 :].strip()
                    current_timeline = f"Between Jul-26 to {date_part}"
            continue
        if "beyond dec" in combined_text:
            current_timeline = "Beyond Dec-25"
            continue

        if sl_no_val.upper() in ["NIL", "NA", "N/A", "NONE"] and not pooling_ss_val:
            continue
        if not sl_no_val and not pooling_ss_val:
            continue
        if "subtotal" in sl_no_lower or "total" in sl_no_lower:
            continue
        if "subtotal" in pooling_ss_lower or "total" in pooling_ss_lower:
            continue

        note_patterns = [
            "in wr,",
            "in sr,",
            "in nr,",
            "in er,",
            "note:",
            "notes:",
            "tr. system",
            "transmission system",
            "planned w/o",
        ]
        if sl_no_val and len(sl_no_val) > 50 and any(pattern in sl_no_lower for pattern in note_patterns):
            print(f"      [Skipping Footer Note in sl_no] {sl_no_val[:80]}...")
            continue
        if (
            pooling_ss_val
            and len(pooling_ss_val) > 50
            and any(pattern in pooling_ss_lower for pattern in note_patterns)
        ):
            print(f"      [Skipping Footer Note in pooling_ss] {pooling_ss_val[:80]}...")
            continue

        if sl_no_val and sl_no_val.isdigit():
            custom_serial_counter += 1
            parent_sl_no = custom_serial_counter
            final_sl_no = str(custom_serial_counter)
        elif sl_no_val and sl_no_val.isalpha() and len(sl_no_val) == 1:
            final_sl_no = f"{parent_sl_no}{sl_no_val}" if parent_sl_no else sl_no_val
        elif not sl_no_val and pooling_ss_val:
            if "subtotal" in pooling_ss_lower or "total" in pooling_ss_lower:
                final_sl_no = pooling_ss_val
            else:
                custom_serial_counter += 1
                parent_sl_no = custom_serial_counter
                final_sl_no = str(custom_serial_counter)
        else:
            final_sl_no = sl_no_val if sl_no_val else None

        clean_pooling_ss, additional_info = extract_additional_info_from_pooling_ss(pooling_ss_val)
        if clean_pooling_ss:
            clean_pooling_ss = clean_margin_substation_name(clean_pooling_ss)

        num_cols = len(row)
        record = {
            "sl_no": final_sl_no,
            "state": normalize_state_name_fn(row.iloc[2]) if num_cols > 2 and pd.notna(row.iloc[2]) else None,
            "region": current_region,
            "pooling_ss": clean_pooling_ss if clean_pooling_ss else None,
            "additional_information_of_pooling_ss": additional_info,
            "timelines": current_timeline,
            "re_potential_mw": _to_margin_numeric(row.iloc[3]) if num_cols > 3 else None,
            "bess_mw": _to_margin_numeric(row.iloc[4]) if num_cols > 4 else None,
            "ss_evacuation_capacity_mw": _to_margin_numeric(row.iloc[5]) if num_cols > 5 else None,
            "expected_cod_of_pooling_station": (
                str(row.iloc[6]).strip()
                if num_cols > 6 and pd.notna(row.iloc[6]) and str(row.iloc[6]).strip() not in ["", "nan"]
                else None
            ),
            "connectivity_granted_1_200kv_mw": _to_margin_numeric(row.iloc[7]) if num_cols > 7 else None,
            "connectivity_granted_1_400kv_mw": _to_margin_numeric(row.iloc[8]) if num_cols > 8 else None,
            "connectivity_granted_1_total_mw": _to_margin_numeric(row.iloc[9]) if num_cols > 9 else None,
            "connectivity_granted_2_200kv_mw": _to_margin_numeric(row.iloc[10]) if num_cols > 10 else None,
            "connectivity_granted_2_400kv_mw": _to_margin_numeric(row.iloc[11]) if num_cols > 11 else None,
            "connectivity_granted_2_total_mw": _to_margin_numeric(row.iloc[12]) if num_cols > 12 else None,
            "margin_for_connectivity_200kv_mw": _to_margin_numeric(row.iloc[13]) if num_cols > 13 else None,
            "margin_for_connectivity_400kv_mw": _to_margin_numeric(row.iloc[14]) if num_cols > 14 else None,
            "margin_for_connectivity_total_mw": _to_margin_numeric(row.iloc[15]) if num_cols > 15 else None,
            "additional_margin_200kv_mw": _to_margin_numeric(row.iloc[16]) if num_cols > 16 else None,
            "additional_margin_400kv_mw": _to_margin_numeric(row.iloc[17]) if num_cols > 17 else None,
            "additional_margin_total_mw": _to_margin_numeric(row.iloc[18]) if num_cols > 18 else None,
            "effectiveness_of_gna": (
                str(row.iloc[19]).strip()
                if num_cols > 19 and pd.notna(row.iloc[19]) and str(row.iloc[19]).strip() not in ["", "nan"]
                else None
            ),
            "remarks": None,
        }
        margin_records.append(record)

    return (
        margin_records,
        current_region,
        current_timeline,
        parent_sl_no,
        custom_serial_counter,
    )


def extract_margin_data(*, normalize_state_name_fn=None, margin_pdf_dir=MARGIN_PDF_DIR):
    """Extract legacy Margin-sheet data from the dedicated Margin PDF folder."""
    if normalize_state_name_fn is None:
        normalize_state_name_fn = normalize_state_name

    print("\n" + "=" * 60)
    print("Margin Sheet Extraction")
    print("=" * 60)

    if not os.path.isdir(margin_pdf_dir):
        print(f"  WARNING: Margin PDF folder not found: {margin_pdf_dir}")
        return []

    pdf_paths = sorted(
        os.path.join(margin_pdf_dir, name)
        for name in os.listdir(margin_pdf_dir)
        if name.lower().endswith(".pdf")
    )
    if not pdf_paths:
        print("  WARNING: No Margin PDFs found.")
        return []

    all_records = []
    parent_sl_no = None
    custom_serial_counter = 0
    for pdf_path in pdf_paths:
        print(f"\n  Processing Margin PDF: {os.path.basename(pdf_path)}")
        try:
            tables = camelot.read_pdf(pdf_path, pages="all", flavor="lattice", suppress_stdout=True)
        except Exception as exc:
            print(f"  WARNING: Margin extraction failed for {os.path.basename(pdf_path)}: {exc}")
            continue

        table_dfs = [table.df for table in tables]
        print(f"    Lattice extraction successful. Found {len(table_dfs)} table(s)")
        if not table_dfs:
            continue

        current_region = None
        current_timeline = None
        pdf_records = []
        is_margin_pdf = False

        for table_idx, table_df in enumerate(table_dfs):
            if table_df.empty or len(table_df.columns) != 20:
                continue

            if table_idx == 0:
                header_text = " ".join(table_df.iloc[0:4].astype(str).values.flatten()).lower()
                if (
                    ("margin for connectivity" in header_text or ("margin" in header_text and "pooling station" in header_text))
                    and not ("allocation" in header_text and "bay" in header_text)
                ):
                    is_margin_pdf = True
                    print(
                        f"    Detected SN9 Margin PDF ({len(table_df.columns)} columns, LATTICE mode)"
                    )
                    print("    Skipping 2 header rows, data/timeline headers start at row 2")
                else:
                    break

            if not is_margin_pdf:
                continue

            if table_idx > 0:
                print(
                    f"    Table {table_idx + 1}: Margin continuation (20 columns), "
                    "processing with SN9 Margin logic"
                )

            data_df = table_df.iloc[2:].reset_index(drop=True)
            (
                margin_records,
                current_region,
                current_timeline,
                parent_sl_no,
                custom_serial_counter,
            ) = extract_margin_records_from_table(
                data_df,
                current_region=current_region,
                current_timeline=current_timeline,
                parent_sl_no=parent_sl_no,
                custom_serial_counter=custom_serial_counter,
                normalize_state_name_fn=normalize_state_name_fn,
            )
            if margin_records:
                pdf_records.extend(margin_records)
                print(
                    f"    Table {table_idx + 1}: Extracted {len(margin_records)} rows "
                    "using SN9 Margin mapping"
                )

        all_records.extend(pdf_records)

    if not all_records:
        print("  WARNING: No Margin records extracted.")
        return []

    print("\n  Applying state propagation from subcomplexes to parent complex rows...")
    all_records = propagate_state_to_parent_complex(all_records)

    print("\n  Post-processing Margin sheet: Cleaning pooling_ss values...")
    cleaned_count = 0
    for record in all_records:
        original_pooling_ss = record.get("pooling_ss", "")
        if original_pooling_ss:
            cleaned_pooling_ss = clean_margin_substation_name(original_pooling_ss)
            if cleaned_pooling_ss != original_pooling_ss:
                cleaned_count += 1
                if cleaned_count <= 5:
                    print(f"      [Clean] '{original_pooling_ss}' -> '{cleaned_pooling_ss}'")
            record["pooling_ss"] = cleaned_pooling_ss
    print(f"      [Summary] Cleaned {cleaned_count} pooling_ss names")

    print("\n  Post-processing Margin sheet: Calculating capacity patterns in Expected CoD...")
    cod_calc_count = 0
    for record in all_records:
        original_cod = record.get("expected_cod_of_pooling_station", "")
        if original_cod:
            calculated_cod = replace_multiplication_patterns(original_cod)
            if calculated_cod != original_cod:
                cod_calc_count += 1
                if cod_calc_count <= 5:
                    print(f"      [Calc] '{original_cod}' -> '{calculated_cod}'")
            record["expected_cod_of_pooling_station"] = calculated_cod
    print(f"      [Summary] Calculated {cod_calc_count} multiplication patterns in Expected CoD")
    print(f"\n  Total Margin records extracted: {len(all_records)}")
    return all_records
