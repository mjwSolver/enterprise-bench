"""
Pytest Configuration & Automated Marker Hook
============================================
Automatically categorizes tests into:
- `unit`: In-memory isolated unit tests (tests/unit/, test_core.py, test_pii_engine.py)
- `integration`: Full generation / I/O tests (tests/ppt_tests/, test_docx_engine.py, test_ppt_engine.py)
- `core`: Core infrastructure tests
- `ppt`: Presentation engine tests
- `docx`: Document compliance engine tests
- `xlsx`: Spreadsheet engine tests
"""

import pytest


def pytest_collection_modifyitems(items):
    for item in items:
        fspath = str(item.fspath)

        # Core / Unit markers
        if "test_core.py" in fspath:
            item.add_marker(pytest.mark.core)
            item.add_marker(pytest.mark.unit)

        if "tests/unit" in fspath or "test_dependencies.py" in fspath:
            item.add_marker(pytest.mark.unit)

        if "test_pii_engine.py" in fspath:
            item.add_marker(pytest.mark.core)
            item.add_marker(pytest.mark.unit)

        # PPT engine markers
        if "ppt_tests" in fspath or "test_ppt_engine.py" in fspath:
            item.add_marker(pytest.mark.ppt)
            item.add_marker(pytest.mark.integration)

        # DOCX engine markers
        if "test_docx_engine.py" in fspath:
            item.add_marker(pytest.mark.docx)
            item.add_marker(pytest.mark.integration)

        # XLSX engine markers
        if "test_xlsx" in fspath or "xlsx_tests" in fspath:
            item.add_marker(pytest.mark.xlsx)
            item.add_marker(pytest.mark.integration)
