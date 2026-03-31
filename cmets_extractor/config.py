from __future__ import annotations

from pathlib import Path


BASE_DIR = str(Path(__file__).resolve().parents[1])
DATA_TO_BE_CAPTURED_PDF_DIR = str(Path(BASE_DIR) / "Data to be captured PDFs")
ELEMENT_STATUS_PDF_DIR = str(Path(BASE_DIR) / "Element Status PDFs")
MARGIN_PDF_DIR = str(Path(BASE_DIR) / "Margin PDFs")

PDF_PATH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "176431229109Minutes of 42nd CMETS NR meeting held on 11-11-2025.pdf"
)
TEMPLATE_EXCEL = str(Path(BASE_DIR) / "Connectivity Application Data.xlsx")
OUTPUT_EXCEL = str(Path(BASE_DIR) / "42nd_34th_CMETS_Extracted_Data_VoltageFix.xlsx")
TARGET_SHEET = "Data to be captured"
BULK_CONSUMERS_SHEET = "Bulk Consumers"

CMETS_MEETING_NUMBER = 42
CMETS_MEETING_DATE = "11.11.2025"

PDF_PATH_43RD = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "177185140447Minutes of 43rd CMETS NR meeting held on 12.01.2026_F.pdf"
)
CMETS_43RD_MEETING_NUMBER = 43
CMETS_43RD_MEETING_DATE = "12.01.2026"

PDF_PATH_33RD = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "172381548953Minutes of 33rd CMETS NR meeting held on 05.08.2024.pdf"
)
CMETS_33RD_MEETING_NUMBER = 33
CMETS_33RD_MEETING_DATE = "05.08.2024"

PDF_PATH_32ND = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "172119609932Minutes of 32nd CMETS NR meeting held on 10-07-24.pdf"
)
CMETS_32ND_MEETING_NUMBER = 32
CMETS_32ND_MEETING_DATE = "10.07.2024"

PDF_PATH_31ST = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "172113371706Minutes of 31st CMETS NR meeting held on 27-06-2024.pdf"
)
CMETS_31ST_MEETING_NUMBER = 31
CMETS_31ST_MEETING_DATE = "27.06.2024"

PDF_PATH_30TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "171924065907Minutes of 30th CMETS-NR Meeting held on 18 06 24.pdf"
)
CMETS_30TH_MEETING_NUMBER = 30
CMETS_30TH_MEETING_DATE = "18.06.2024"

PDF_PATH_29TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "171635517804Minutes 29th CMETS-NR Meeting.pdf"
)
CMETS_29TH_MEETING_NUMBER = 29
CMETS_29TH_MEETING_DATE = "17.05.2024"

PDF_PATH_28TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "171257051020Minutes of 28th CMETS-NR.pdf"
)
CMETS_28TH_MEETING_NUMBER = 28
CMETS_28TH_MEETING_DATE = "27.03.2024"

PDF_PATH_27TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "170643184951Minutes of 27th CMETS-NR Meeting 10 01 24.pdf"
)
CMETS_27TH_MEETING_NUMBER = 27
CMETS_27TH_MEETING_DATE = "10.01.2024"

PDF_PATH_26TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "170309384420Minutes of 26th CMETS NR Meeting.pdf"
)
CMETS_26TH_MEETING_NUMBER = 26
CMETS_26TH_MEETING_DATE = "01.12.2023"

PDF_PATH_25TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "170019482233MOM 25th CMETS-NR meeting Final.pdf"
)
CMETS_25TH_MEETING_NUMBER = 25
CMETS_25TH_MEETING_DATE = "31.10.2023"

PDF_PATH_24TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "169642938440Minutes of 24th CMETS-NR meeting held on 20.09.2023.pdf"
)
CMETS_24TH_MEETING_NUMBER = 24
CMETS_24TH_MEETING_DATE = "20.09.2023"

PDF_PATH_23RD = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "169614651228Minutes of 23rd CMETS NR held on 29-08-23.pdf"
)
CMETS_23RD_MEETING_NUMBER = 23
CMETS_23RD_MEETING_DATE = "29.08.2023"

PDF_PATH_22ND = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "169500987876Minutes of 22nd CMETS NR held on 21.08.2023.pdf"
)
CMETS_22ND_MEETING_NUMBER = 22
CMETS_22ND_MEETING_DATE = "21.08.2023"

PDF_PATH_21ST = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "169347933472Minute Notice & Minutes of 21st CMETS-NR.pdf"
)
CMETS_21ST_MEETING_NUMBER = 21
CMETS_21ST_MEETING_DATE = "31.07.2023"

PDF_PATH_20TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "168930751455Minutes_20th CMETS-NR.pdf"
)
CMETS_20TH_MEETING_NUMBER = 20
CMETS_20TH_MEETING_DATE = "30.06.2023"

PDF_PATH_19TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "168631891938Minutes_19th NR-CMETS.pdf"
)
CMETS_19TH_MEETING_NUMBER = 19
CMETS_19TH_MEETING_DATE = "31.05.2023"

PDF_PATH_18TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "16842966352418th NR-CMETS_Minutes.pdf"
)
CMETS_18TH_MEETING_NUMBER = 18
CMETS_18TH_MEETING_DATE = "28.04.2023"

PDF_PATH_17TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "168423311128Minutes_17th CMETS-NR.pdf"
)
CMETS_17TH_MEETING_NUMBER = 17
CMETS_17TH_MEETING_DATE = "31.03.2023"

PDF_PATH_16TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "168234133985Minutes_16th CMETS-NR.pdf"
)
CMETS_16TH_MEETING_NUMBER = 16
CMETS_16TH_MEETING_DATE = "28.02.2023"

PDF_PATH_15TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "167809718034Minutes_15th NR-CMETS(1).pdf"
)
CMETS_15TH_MEETING_NUMBER = 15
CMETS_15TH_MEETING_DATE = "27.02.2023"

PDF_PATH_14TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "167404853372Minutes_14th CMETS-NR.pdf"
)
CMETS_14TH_MEETING_NUMBER = 14
CMETS_14TH_MEETING_DATE = "23.12.2022"

PDF_PATH_34TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "172838877090Minutes of meeting 34th CMETS NR Meeting held on 20-9-24.pdf"
)
CMETS_34TH_MEETING_NUMBER = 34
CMETS_34TH_MEETING_DATE = "20.09.2024"

PDF_PATH_35TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "173160228632Minutes of 35th CMETS NR meeting held on 29-10-2024.pdf"
)
CMETS_35TH_MEETING_NUMBER = 35
CMETS_35TH_MEETING_DATE = "29.10.2024"

RE_EFFECTIVENESS_PDF_OCT = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR) / "176586184113pdf_RE effectiveness Oct 25.pdf"
)
RE_EFFECTIVENESS_PDF_SEP = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR) / "176586182296pdf_RE effectiveness Sept 25.pdf"
)
RE_EFFECTIVENESS_PDF_DEC = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR) / "177157746921Tobemadeeffective_CMU_Dec25.pdf"
)

PDF_PATH_39TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "175733735430Minutes of 39th CMETS NR meeting held on 28-07-2025.pdf"
)
CMETS_39TH_MEETING_NUMBER = 39
CMETS_39TH_MEETING_DATE = "28.07.2025"

PDF_PATH_40TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR) / "175923696873MoM  40th CMETS NR meeting_F.pdf"
)
CMETS_40TH_MEETING_NUMBER = 40
CMETS_40TH_MEETING_DATE = "12.09.2025"

PDF_PATH_41ST = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "176242143922Minutes of 41st CMETS NR meeting held on 10-10-2025.pdf"
)
CMETS_41ST_MEETING_NUMBER = 41
CMETS_41ST_MEETING_DATE = "10.10.2025"

PDF_PATH_38TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "175128955300Minutes of 38th CMETS NR meeting held on 28-05-2025.pdf"
)
CMETS_38TH_MEETING_NUMBER = 38
CMETS_38TH_MEETING_DATE = "28.05.2025"

PDF_PATH_37TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR)
    / "174754675775Minutes of 37th CMETS NR meeting held on 27-03-2025.pdf"
)
CMETS_37TH_MEETING_NUMBER = 37
CMETS_37TH_MEETING_DATE = "27.03.2025"

PDF_PATH_36TH = str(
    Path(DATA_TO_BE_CAPTURED_PDF_DIR) / "174039880458Minutes 36th CMETS NR Meeting 15.01.25.pdf"
)
CMETS_36TH_MEETING_NUMBER = 36
CMETS_36TH_MEETING_DATE = "15.01.2025"

TBCB_PDF_PATH = str(Path(ELEMENT_STATUS_PDF_DIR) / "Report_TBCB_UC.pdf")
RTM_PDF_PATH = str(Path(ELEMENT_STATUS_PDF_DIR) / "RTM_UC.pdf")
NCT_PDF_PATH = str(Path(ELEMENT_STATUS_PDF_DIR) / "35th_NCT_MoM.pdf")
ELEMENT_STATUS_SHEET = "Element Status"
MARGIN_SHEET = "Margin"
ELEMENT_STATUS_TARGET_TEXT = "Monitoring Report of Under Construction TBCB Projects"
RTM_ELEMENT_STATUS_TARGET_TEXTS = (
    "Monitoring Report of Under Construction RTM Projects",
    "Real Time Monitoring",
)

MARGIN_FIELDS = [
    "sl_no",
    "state",
    "region",
    "pooling_ss",
    "additional_information_of_pooling_ss",
    "timelines",
    "re_potential_mw",
    "bess_mw",
    "ss_evacuation_capacity_mw",
    "expected_cod_of_pooling_station",
    "connectivity_granted_1_200kv_mw",
    "connectivity_granted_1_400kv_mw",
    "connectivity_granted_1_total_mw",
    "connectivity_granted_2_200kv_mw",
    "connectivity_granted_2_400kv_mw",
    "connectivity_granted_2_total_mw",
    "margin_for_connectivity_200kv_mw",
    "margin_for_connectivity_400kv_mw",
    "margin_for_connectivity_total_mw",
    "additional_margin_200kv_mw",
    "additional_margin_400kv_mw",
    "additional_margin_total_mw",
    "effectiveness_of_gna",
    "remarks",
]

STATE_NAME_MAP = {
    "Andhra Pradesh": "Andhra Pradesh",
    "Arunachal Pradesh": "Arunachal Pradesh",
    "Assam": "Assam",
    "Bihar": "Bihar",
    "Chhattisgarh": "Chhattisgarh",
    "Goa": "Goa",
    "Gujarat": "Gujarat",
    "Haryana": "Haryana",
    "Himachal Pradesh": "Himachal Pradesh",
    "Jharkhand": "Jharkhand",
    "Karnataka": "Karnataka",
    "Kerala": "Kerala",
    "Madhya Pradesh": "Madhya Pradesh",
    "Maharashtra": "Maharashtra",
    "Manipur": "Manipur",
    "Meghalaya": "Meghalaya",
    "Mizoram": "Mizoram",
    "Nagaland": "Nagaland",
    "Odisha": "Odisha",
    "Punjab": "Punjab",
    "Rajasthan": "Rajasthan",
    "Sikkim": "Sikkim",
    "Tamil Nadu": "Tamil Nadu",
    "Telangana": "Telangana",
    "Tripura": "Tripura",
    "Uttar Pradesh": "Uttar Pradesh",
    "Uttarakhand": "Uttarakhand",
    "West Bengal": "West Bengal",
    "Ladakh": "Ladakh",
    "Jammu and Kashmir": "Jammu and Kashmir",
    "J&K": "Jammu and Kashmir",
    "AP": "Andhra Pradesh",
    "AR": "Arunachal Pradesh",
    "AS": "Assam",
    "BR": "Bihar",
    "CG": "Chhattisgarh",
    "GA": "Goa",
    "GJ": "Gujarat",
    "HR": "Haryana",
    "HP": "Himachal Pradesh",
    "JH": "Jharkhand",
    "KA": "Karnataka",
    "KL": "Kerala",
    "MP": "Madhya Pradesh",
    "MH": "Maharashtra",
    "MN": "Manipur",
    "ML": "Meghalaya",
    "MZ": "Mizoram",
    "NL": "Nagaland",
    "OD": "Odisha",
    "OR": "Odisha",
    "PB": "Punjab",
    "RJ": "Rajasthan",
    "SK": "Sikkim",
    "TN": "Tamil Nadu",
    "TS": "Telangana",
    "TG": "Telangana",
    "TR": "Tripura",
    "UP": "Uttar Pradesh",
    "UK": "Uttarakhand",
    "UT": "Uttarakhand",
    "WB": "West Bengal",
    "LA": "Ladakh",
    "JK": "Jammu and Kashmir",
}

EXCEL_COLUMNS = {
    "sr_no": 2,
    "region": 3,
    "state": 4,
    "substation": 5,
    "name_of_developers": 7,
    "gna_st_ii_application_id": 9,
    "lta_application_id": 10,
    "application_id_enhancement_5_2_or_revision": 11,
    "cmets_gna_approved": 12,
    "cmets_lta_approved": 13,
    "cmets_gna_meeting_date": 14,
    "cmets_lta_meeting_date": 15,
    "type": 16,
    "application_quantum_mw": 17,
    "granted_quantum_mw": 18,
    "installed_breakup_solar_mw": 19,
    "installed_breakup_wind_mw": 20,
    "installed_breakup_hybrid_mw": 21,
    "installed_breakup_hydro_mw": 22,
    "battery_mwh": 23,
    "battery_injection_mw": 24,
    "psp_injection_mw": 27,
    "psp_drawl_mw": 28,
    "application_date": 31,
    "mode_criteria": 32,
    "applied_start_date": 33,
    "gna_operationalization_date": 34,
    "gna_operationalization_yes_no": 35,
    "date_for_additional_capacity": 36,
    "nature_of_applicant": 37,
    "status_of_application": 38,
    "voltage_level_kv": 39,
    "cts_element_unique_code": 41,
    "ats_element_unique_code": 42,
    "dtl_element_unique_code": 43,
}

DATA_CAPTURE_DATE_FIELDS = {
    "application_date",
    "cmets_gna_meeting_date",
    "cmets_lta_meeting_date",
    "applied_start_date",
    "gna_operationalization_date",
    "date_for_additional_capacity",
}

DATA_CAPTURE_NUMERIC_FIELDS = {
    "cmets_gna_approved",
    "cmets_lta_approved",
    "application_quantum_mw",
    "granted_quantum_mw",
    "installed_breakup_solar_mw",
    "installed_breakup_wind_mw",
    "installed_breakup_hybrid_mw",
    "installed_breakup_hydro_mw",
    "battery_mwh",
    "battery_injection_mw",
    "psp_injection_mw",
    "psp_drawl_mw",
    "voltage_level_kv",
}

BULK_CONSUMERS_COLUMNS = {
    "sr_no": 2,
    "region": 3,
    "state": 4,
    "substation": 5,
    "name_of_developers": 6,
    "group": 7,
    "gna_application_id": 8,
    "cmets_gna_approved": 9,
    "cmets_gna_meeting_date": 10,
    "gna_type": 11,
    "quantum_within_region_mw": 12,
    "quantum_outside_region_mw": 13,
    "total_quantum_mw": 14,
    "nature_of_applicant": 15,
    "status_of_application": 16,
    "start_date_of_gna": 17,
    "end_date_of_gna": 18,
}

BULK_CONSUMERS_DATE_FIELDS = {
    "cmets_gna_meeting_date",
    "start_date_of_gna",
    "end_date_of_gna",
}

BULK_CONSUMERS_NUMERIC_FIELDS = {
    "cmets_gna_approved",
    "quantum_within_region_mw",
    "quantum_outside_region_mw",
    "total_quantum_mw",
}

STATE_TO_REGION = {
    "rajasthan": "NR",
    "punjab": "NR",
    "haryana": "NR",
    "uttar pradesh": "NR",
    "up": "NR",
    "himachal pradesh": "NR",
    "hp": "NR",
    "uttarakhand": "NR",
    "jammu and kashmir": "NR",
    "j&k": "NR",
    "delhi": "NR",
    "chandigarh": "NR",
    "ladakh": "NR",
    "tamil nadu": "SR",
    "karnataka": "SR",
    "andhra pradesh": "SR",
    "ap": "SR",
    "telangana": "SR",
    "kerala": "SR",
    "puducherry": "SR",
    "pondicherry": "SR",
    "gujarat": "WR",
    "maharashtra": "WR",
    "madhya pradesh": "WR",
    "mp": "WR",
    "goa": "WR",
    "chhattisgarh": "WR",
    "daman": "WR",
    "diu": "WR",
    "dadra": "WR",
    "west bengal": "ER",
    "bihar": "ER",
    "odisha": "ER",
    "orissa": "ER",
    "jharkhand": "ER",
    "assam": "NER",
    "manipur": "NER",
    "meghalaya": "NER",
    "tripura": "NER",
    "nagaland": "NER",
    "arunachal pradesh": "NER",
    "mizoram": "NER",
    "sikkim": "NER",
}

SUBSTATION_REGION_MAP = {
    "bikaner": "NR",
    "fatehgarh": "NR",
    "bhadla": "NR",
    "barmer": "NR",
    "jaisalmer": "NR",
    "jodhpur": "NR",
    "sirohi": "NR",
    "merta": "NR",
    "nagaur": "NR",
    "pali": "NR",
    "jalore": "NR",
    "ramgarh": "NR",
    "neemrana": "NR",
    "kotputli": "NR",
    "rishabhdeo": "NR",
}

SUBSTATION_STATE_MAP = {
    "allahabad": "Uttar Pradesh",
    "barmer": "Rajasthan",
    "beawar": "Rajasthan",
    "bhadla": "Rajasthan",
    "bikaner": "Rajasthan",
    "chittorgarh": "Rajasthan",
    "debari": "Rajasthan",
    "gajraula": "Uttar Pradesh",
    "jalore": "Rajasthan",
    "jind": "Haryana",
    "kankroli": "Rajasthan",
    "karkardooma": "Delhi",
    "kotputli": "Rajasthan",
    "mainpuri": "Uttar Pradesh",
    "masjid mod": "Delhi",
    "merta": "Rajasthan",
    "nagaur": "Rajasthan",
    "neemrana": "Rajasthan",
    "pali": "Rajasthan",
    "ramgarh": "Rajasthan",
    "rishabhdeo": "Rajasthan",
    "sector 148": "Uttar Pradesh",
    "sirohi": "Rajasthan",
    "vsnl": "Delhi",
    "wadala granthian": "Punjab",
}

REGION_TO_STATE = {
    "NR": "Rajasthan",
    "SR": "Tamil Nadu",
    "WR": "Gujarat",
    "ER": "West Bengal",
    "NER": "Assam",
}

__all__ = [
    "BASE_DIR",
    "DATA_TO_BE_CAPTURED_PDF_DIR",
    "ELEMENT_STATUS_PDF_DIR",
    "MARGIN_PDF_DIR",
    "PDF_PATH",
    "TEMPLATE_EXCEL",
    "OUTPUT_EXCEL",
    "TARGET_SHEET",
    "BULK_CONSUMERS_SHEET",
    "CMETS_MEETING_NUMBER",
    "CMETS_MEETING_DATE",
    "PDF_PATH_43RD",
    "CMETS_43RD_MEETING_NUMBER",
    "CMETS_43RD_MEETING_DATE",
    "PDF_PATH_33RD",
    "CMETS_33RD_MEETING_NUMBER",
    "CMETS_33RD_MEETING_DATE",
    "PDF_PATH_32ND",
    "CMETS_32ND_MEETING_NUMBER",
    "CMETS_32ND_MEETING_DATE",
    "PDF_PATH_31ST",
    "CMETS_31ST_MEETING_NUMBER",
    "CMETS_31ST_MEETING_DATE",
    "PDF_PATH_30TH",
    "CMETS_30TH_MEETING_NUMBER",
    "CMETS_30TH_MEETING_DATE",
    "PDF_PATH_29TH",
    "CMETS_29TH_MEETING_NUMBER",
    "CMETS_29TH_MEETING_DATE",
    "PDF_PATH_28TH",
    "CMETS_28TH_MEETING_NUMBER",
    "CMETS_28TH_MEETING_DATE",
    "PDF_PATH_27TH",
    "CMETS_27TH_MEETING_NUMBER",
    "CMETS_27TH_MEETING_DATE",
    "PDF_PATH_26TH",
    "CMETS_26TH_MEETING_NUMBER",
    "CMETS_26TH_MEETING_DATE",
    "PDF_PATH_25TH",
    "CMETS_25TH_MEETING_NUMBER",
    "CMETS_25TH_MEETING_DATE",
    "PDF_PATH_24TH",
    "CMETS_24TH_MEETING_NUMBER",
    "CMETS_24TH_MEETING_DATE",
    "PDF_PATH_23RD",
    "CMETS_23RD_MEETING_NUMBER",
    "CMETS_23RD_MEETING_DATE",
    "PDF_PATH_22ND",
    "CMETS_22ND_MEETING_NUMBER",
    "CMETS_22ND_MEETING_DATE",
    "PDF_PATH_21ST",
    "CMETS_21ST_MEETING_NUMBER",
    "CMETS_21ST_MEETING_DATE",
    "PDF_PATH_20TH",
    "CMETS_20TH_MEETING_NUMBER",
    "CMETS_20TH_MEETING_DATE",
    "PDF_PATH_19TH",
    "CMETS_19TH_MEETING_NUMBER",
    "CMETS_19TH_MEETING_DATE",
    "PDF_PATH_18TH",
    "CMETS_18TH_MEETING_NUMBER",
    "CMETS_18TH_MEETING_DATE",
    "PDF_PATH_17TH",
    "CMETS_17TH_MEETING_NUMBER",
    "CMETS_17TH_MEETING_DATE",
    "PDF_PATH_16TH",
    "CMETS_16TH_MEETING_NUMBER",
    "CMETS_16TH_MEETING_DATE",
    "PDF_PATH_15TH",
    "CMETS_15TH_MEETING_NUMBER",
    "CMETS_15TH_MEETING_DATE",
    "PDF_PATH_14TH",
    "CMETS_14TH_MEETING_NUMBER",
    "CMETS_14TH_MEETING_DATE",
    "PDF_PATH_34TH",
    "CMETS_34TH_MEETING_NUMBER",
    "CMETS_34TH_MEETING_DATE",
    "PDF_PATH_35TH",
    "CMETS_35TH_MEETING_NUMBER",
    "CMETS_35TH_MEETING_DATE",
    "RE_EFFECTIVENESS_PDF_OCT",
    "RE_EFFECTIVENESS_PDF_SEP",
    "RE_EFFECTIVENESS_PDF_DEC",
    "PDF_PATH_39TH",
    "CMETS_39TH_MEETING_NUMBER",
    "CMETS_39TH_MEETING_DATE",
    "PDF_PATH_40TH",
    "CMETS_40TH_MEETING_NUMBER",
    "CMETS_40TH_MEETING_DATE",
    "PDF_PATH_41ST",
    "CMETS_41ST_MEETING_NUMBER",
    "CMETS_41ST_MEETING_DATE",
    "PDF_PATH_38TH",
    "CMETS_38TH_MEETING_NUMBER",
    "CMETS_38TH_MEETING_DATE",
    "PDF_PATH_37TH",
    "CMETS_37TH_MEETING_NUMBER",
    "CMETS_37TH_MEETING_DATE",
    "PDF_PATH_36TH",
    "CMETS_36TH_MEETING_NUMBER",
    "CMETS_36TH_MEETING_DATE",
    "TBCB_PDF_PATH",
    "RTM_PDF_PATH",
    "NCT_PDF_PATH",
    "ELEMENT_STATUS_SHEET",
    "MARGIN_SHEET",
    "ELEMENT_STATUS_TARGET_TEXT",
    "RTM_ELEMENT_STATUS_TARGET_TEXTS",
    "MARGIN_FIELDS",
    "STATE_NAME_MAP",
    "EXCEL_COLUMNS",
    "DATA_CAPTURE_DATE_FIELDS",
    "DATA_CAPTURE_NUMERIC_FIELDS",
    "BULK_CONSUMERS_COLUMNS",
    "BULK_CONSUMERS_DATE_FIELDS",
    "BULK_CONSUMERS_NUMERIC_FIELDS",
    "STATE_TO_REGION",
    "SUBSTATION_REGION_MAP",
    "SUBSTATION_STATE_MAP",
    "REGION_TO_STATE",
]
