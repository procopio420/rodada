from pathlib import Path

import pytest

from modules.documents_printing.renderers import render_escpos, render_html, render_text
from tests.printing_fixture import receipt_fixture

ROOT = Path(__file__).parent / "fixtures" / "printing"


@pytest.mark.parametrize(
    "kind",
    [
        "CUSTOMER_CHECK",
        "PAYMENT_RECEIPT",
        "PARTIAL_PAYMENT_RECEIPT",
        "CLOSED_TAB_RECEIPT",
        "PRODUCTION_TICKET",
    ],
)
@pytest.mark.parametrize("width", [58, 80])
@pytest.mark.parametrize("copy", [False, True])
def test_version_one_golden_outputs(kind, width, copy):
    document = receipt_fixture(kind)
    name = f"{kind}-{width}-{'copy' if copy else 'original'}"
    assert render_text(document, width, copy) == (ROOT / (name + ".txt")).read_text(encoding="utf-8")
    assert render_html(document, width, copy) == (ROOT / (name + ".html")).read_text(encoding="utf-8")
    assert (
        render_escpos(document, width, copy).hex() == (ROOT / (name + ".hex")).read_text(encoding="utf-8").strip()
    )
