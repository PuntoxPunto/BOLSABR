from datetime import date
from decimal import Decimal

from bolsabr.b3.corporate_actions import _encoded_params, _optional_date


def test_b3_listed_companies_params_are_compact_json_base64():
    token = _encoded_params(
        tradingName="PETROBRAS",
        language="pt-br",
        pageNumber=1,
        pageSize=99999,
    )
    assert token.startswith("eyJ")
    assert "\n" not in token


def test_optional_date_accepts_b3_pt_br_dates():
    assert _optional_date("21/08/2026") == date(2026, 8, 21)
    assert _optional_date(None) is None
