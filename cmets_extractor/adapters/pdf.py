from __future__ import annotations

import camelot
import pdfplumber

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None


def get_pdf_page_count(pdf_path):
    """Return page count using pdfplumber first, with pypdf fallback."""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            return len(pdf.pages)
    except Exception:
        if PdfReader is None:
            raise
        return len(PdfReader(pdf_path).pages)


def read_camelot_lattice_tables_chunked(pdf_path, chunk_size=20, start_page=1, end_page=None):
    """
    Read lattice tables incrementally to avoid OpenCV memory spikes on large PDFs.
    Falls back to smaller page ranges when Camelot fails on a chunk.
    """
    page_count = get_pdf_page_count(pdf_path)
    start_page = max(1, int(start_page))
    end_page = page_count if end_page is None else min(page_count, int(end_page))
    if start_page > end_page:
        return []
    all_tables = []

    def read_range(range_start, range_end):
        page_spec = str(range_start) if range_start == range_end else f"{range_start}-{range_end}"
        try:
            return list(camelot.read_pdf(pdf_path, pages=page_spec, flavor="lattice"))
        except Exception as exc:
            if range_start == range_end:
                print(f"  WARNING: Camelot skipped page {page_spec}: {exc}")
                return []

            mid_page = (range_start + range_end) // 2
            print(
                f"  WARNING: Camelot failed on pages {page_spec}; retrying "
                f"{range_start}-{mid_page} and {mid_page + 1}-{range_end}"
            )
            return read_range(range_start, mid_page) + read_range(mid_page + 1, range_end)

    for current_start in range(start_page, end_page + 1, chunk_size):
        current_end = min(end_page, current_start + chunk_size - 1)
        all_tables.extend(read_range(current_start, current_end))

    return all_tables
