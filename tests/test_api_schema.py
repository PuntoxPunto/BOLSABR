from datetime import date
from decimal import Decimal

from bolsabr.api_schema import option_chain_to_dict
from bolsabr.b3.cotahist import CotahistRecord
from bolsabr.chain import build_option_chain


def test_option_chain_api_schema_exposes_market_quality_and_analytics_inputs():
    ref = date(2026, 9, 22)
    chain = build_option_chain(
        underlying="PETR4",
        ref_date=ref,
        instrument_rows=[
            {
                "TckrSymb": "PETRV400W4",
                "Asst": "PETR4",
                "OptnTp": "Put",
                "ExrcPric": "40,00",
                "XprtnDt": "2026-10-16",
                "OptnStyle": "EURO",
            }
        ],
        trade_rows=[
            {
                "RptDt": "22/09/2026",
                "TckrSymb": "PETR4",
                "LastPric": "48,35",
                "MinPric": "48,00",
                "MaxPric": "49,00",
                "TradAvrgPric": "48,50",
                "TradQty": "100",
                "FinInstrmQty": "1000000",
                "NtlFinVol": "48350000",
            },
            {
                "RptDt": "22/09/2026",
                "TckrSymb": "PETRV400W4",
                "LastPric": "0,50",
                "MinPric": "0,40",
                "MaxPric": "0,60",
                "TradAvrgPric": "0,50",
                "TradQty": "25",
                "FinInstrmQty": "2500",
                "NtlFinVol": "1250",
            },
        ],
        open_interest_rows=[
            {
                "RptDt": "22/09/2026",
                "TckrSymb": "PETRV400W4",
                "OpnIntrst": "10000",
                "TtlPos": "10000",
            }
        ],
        cotahist_rows=[
            CotahistRecord(
                ref,
                "82",
                "PETRV400W4",
                80,
                Decimal("0.40"),
                Decimal("0.60"),
                Decimal("0.40"),
                Decimal("0.50"),
                Decimal("0.50"),
                Decimal("0.45"),
                Decimal("0.55"),
                25,
                2500,
                Decimal("1250"),
                Decimal("40"),
                date(2026, 10, 16),
                1,
                "BRTEST",
            )
        ],
        risk_free_rate=0.12,
    )

    payload = option_chain_to_dict(chain)
    assert payload["schema_version"] == "0.1"
    assert payload["underlying"]["ticker"] == "PETR4"
    assert payload["expirations"][0]["type"] == "WEEKLY"
    assert payload["expirations"][0]["dte_business"] is not None

    leg = payload["expirations"][0]["rows"][0]["put"]
    assert leg["market"]["quote_state"] == "TWO_SIDED"
    assert leg["market"]["trade_count"] == 25
    assert leg["analytics_input"]["price_basis"] == "MID"
    assert "iv" in leg["analytics"]
