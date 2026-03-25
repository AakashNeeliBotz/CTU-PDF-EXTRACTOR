from __future__ import annotations

from typing import TypedDict


class MeetingSpec(TypedDict):
    label: str
    number: int
    date: str
    pdf_path: str


class DataCaptureRecord(TypedDict, total=False):
    application_date: str
    name_of_developers: str
    mode_criteria: str
    applied_start_date: str
    gna_st_ii_application_id: str
    lta_application_id: str
    cmets_gna_approved: int
    cmets_lta_approved: int
    cmets_gna_meeting_date: str
    cmets_lta_meeting_date: str
    state: str
    region: str
    nature_of_applicant: str
    application_quantum_mw: float
    type: str
    installed_breakup_solar_mw: float
    installed_breakup_wind_mw: float
    installed_breakup_hybrid_mw: float
    installed_breakup_hydro_mw: float
    battery_mwh: float
    battery_injection_mw: float
    psp_injection_mw: float
    psp_drawl_mw: float
    status_of_application: str
    substation: str
    voltage_level_kv: float
    granted_quantum_mw: float
    application_id_enhancement_5_2_or_revision: str
    date_for_additional_capacity: str
    gna_operationalization_date: str
    gna_operationalization_yes_no: str
    ats_element_unique_code: str
    dtl_element_unique_code: str
    cts_element_unique_code: str
    _partial_row: bool
    _explicit_type_breakup: bool
    _existing_connectivity_quantum: float
    _incremental_re_component_addition: str
    _capacity_headline_total: float


class BulkConsumerRecord(TypedDict, total=False):
    region: str
    state: str
    substation: str
    name_of_developers: str
    group: str
    gna_application_id: str
    cmets_gna_approved: int
    cmets_gna_meeting_date: str
    gna_type: str
    quantum_within_region_mw: float
    quantum_outside_region_mw: float
    total_quantum_mw: float
    nature_of_applicant: str
    status_of_application: str
    start_date_of_gna: str
    end_date_of_gna: str


class MarginRecord(TypedDict, total=False):
    sl_no: str
    state: str
    region: str
    pooling_ss: str
    additional_information_of_pooling_ss: str
    timelines: str
    re_potential_mw: float
    bess_mw: float
    ss_evacuation_capacity_mw: float
    expected_cod_of_pooling_station: str
    connectivity_granted_1_200kv_mw: float
    connectivity_granted_1_400kv_mw: float
    connectivity_granted_1_total_mw: float
    connectivity_granted_2_200kv_mw: float
    connectivity_granted_2_400kv_mw: float
    connectivity_granted_2_total_mw: float
    margin_for_connectivity_200kv_mw: float
    margin_for_connectivity_400kv_mw: float
    margin_for_connectivity_total_mw: float
    additional_margin_200kv_mw: float
    additional_margin_400kv_mw: float
    additional_margin_total_mw: float
    effectiveness_of_gna: str
    remarks: str


class ElementStatusSourceRow(TypedDict, total=False):
    ElementCode: str
    Scope: str
    InterIntra: str
    Scheme: str
    MVA: float
    Mode: str
    AwardedTo: str
    SPV: str
    Length: float
    Locs: float
    Found: float
    Erect: float
    String: float
    Civil: float
    EqptRec: float
    EqptEre: float
    OrgSCOD: str
    AntSCOD: str
    Remarks: str
