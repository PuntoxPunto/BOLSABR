from datetime import date
from decimal import Decimal

from bolsabr.b3.corporate_actions import (
    _cash_distribution_from_supplement,
    _encoded_params,
    _optional_date,
)


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



def test_parse_supplement_cash_distribution_by_isin():
    item = _cash_distribution_from_supplement(
        {
            "assetIssued": "BRPETRACNPR6",
            "paymentDate": "21/12/2026",
            "rate": "0,47156696000",
            "relatedTo": "Anual/2026",
            "approvedOn": "06/08/2026",
            "isinCode": "BRPETRACNPR6",
            "label": "DIVIDENDO",
            "lastDatePrior": "21/08/2026",
            "remarks": "",
        }
    )
    assert item.isin == "BRPETRACNPR6"
    assert item.stock_type == "PN"
    assert item.corporate_action == "DIVIDENDO"
    assert item.last_date_with_rights == date(2026, 8, 21)
    assert item.payment_date == date(2026, 12, 21)
    assert item.value_cash == Decimal("0.47156696000")
