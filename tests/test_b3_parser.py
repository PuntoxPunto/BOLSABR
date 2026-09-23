from bolsabr.b3.client import parse_b3_csv
from bolsabr.b3.normalize import br_decimal, normalize_open_interest, normalize_option_contract


def test_parser_handles_status_and_quoted_semicolon():
    payload = (
        "Status do Arquivo: Final\n"
        'RptDt;TckrSymb;CrpnNm\n'
        '22/09/2026;PETR4;"PETROLEO; BRASILEIRO"\n'
    ).encode("iso-8859-1")
    parsed = parse_b3_csv(payload)
    assert parsed.status == "Final"
    assert parsed.columns == ("RptDt", "TckrSymb", "CrpnNm")
    assert parsed.rows[0]["CrpnNm"] == "PETROLEO; BRASILEIRO"


def test_parser_handles_derivatives_without_status_line():
    parsed = parse_b3_csv("RptDt;TckrSymb;OpnIntrst\n22/09/2026;PETRA400;1200\n")
    assert parsed.status == ""
    assert parsed.rows[0]["OpnIntrst"] == "1200"


def test_br_decimal_accepts_pt_br():
    assert str(br_decimal("1.234,56")) == "1234.56"


def test_option_contract_normalization():
    row = {
        "TckrSymb": "PETRA400",
        "UndrlygTckrSymb1": "PETR4",
        "OptnTp": "Call",
        "ExrcPric": "40,00",
        "XprtnDt": "2026-10-16",
        "OptnStyle": "AMER",
        "CtrctMltplr": "1",
        "ISIN": "BRTEST000000",
    }
    option = normalize_option_contract(row)
    assert option.ticker == "PETRA400"
    assert option.option_type == "CALL"
    assert option.exercise_style == "AMERICAN"
    assert str(option.strike) == "40.00"


def test_open_interest_falls_back_to_total_position():
    oi = normalize_open_interest(
        {
            "RptDt": "22/09/2026",
            "TckrSymb": "PETRA400",
            "OpnIntrst": "",
            "TtlPos": "1500",
            "VartnOpnIntrst": "25",
            "CvrdQty": "1000",
            "UcvrdQty": "500",
        }
    )
    assert oi.open_interest == 1500
    assert oi.total_position == 1500


def test_option_contract_normalization_uses_live_b3_asset_field():
    option = normalize_option_contract(
        {
            "TckrSymb": "PETRA243",
            "Asst": "PETR4",
            "SgmtNm": "EQUITY CALL",
            "OptnTp": "Call",
            "ExrcPric": "21,19",
            "XprtnDt": "2027-01-15",
            "OptnStyle": "AMER",
        }
    )
    assert option.underlying == "PETR4"
    assert option.ticker == "PETRA243"
    assert str(option.strike) == "21.19"
