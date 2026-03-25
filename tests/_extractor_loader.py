from __future__ import annotations

import importlib
import sys
import types
from typing import Any

from tests._helpers import ensure_repo_root_on_path


def _install_stub_modules() -> None:
    camelot = types.ModuleType("camelot")
    camelot.read_pdf = lambda *args, **kwargs: []
    sys.modules.setdefault("camelot", camelot)

    fitz = types.ModuleType("fitz")
    fitz.open = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("fitz stub"))
    sys.modules.setdefault("fitz", fitz)

    pdfplumber = types.ModuleType("pdfplumber")
    pdfplumber.open = lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("pdfplumber stub"))
    sys.modules.setdefault("pdfplumber", pdfplumber)

    pandas = types.ModuleType("pandas")

    def _isna(value: Any) -> bool:
        return value is None

    class _DataFrame(list):
        pass

    pandas.isna = _isna
    pandas.DataFrame = _DataFrame
    sys.modules.setdefault("pandas", pandas)

    openpyxl = types.ModuleType("openpyxl")
    openpyxl.load_workbook = lambda *args, **kwargs: (_ for _ in ()).throw(
        RuntimeError("openpyxl stub")
    )
    sys.modules.setdefault("openpyxl", openpyxl)

    pypdf = types.ModuleType("pypdf")

    class _PdfReader:
        def __init__(self, *args, **kwargs) -> None:
            self.pages = []

    pypdf.PdfReader = _PdfReader
    sys.modules.setdefault("pypdf", pypdf)


def load_extractor():
    ensure_repo_root_on_path()
    try:
        return importlib.import_module("extract_42nd_cmets")
    except ModuleNotFoundError as exc:
        if exc.name not in {
            "camelot",
            "fitz",
            "pdfplumber",
            "pandas",
            "openpyxl",
            "pypdf",
        }:
            raise
        _install_stub_modules()
        return importlib.import_module("extract_42nd_cmets")
