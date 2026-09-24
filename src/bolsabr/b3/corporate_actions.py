from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from bolsabr.b3.normalize import br_decimal, parse_date

BASE_URL = "https://sistemaswebb3-listados.b3.com.br/listedCompaniesProxy/CompanyCall"


@dataclass(frozen=True)
class ListedCompany:
    issuing_company: str
    trading_name: str
    code_cvm: str | None
    raw: dict[str, Any]


@dataclass(frozen=True)
class CashDistribution:
    stock_type: str
    corporate_action: str
    approval_date: date | None
    last_date_with_rights: date | None
    value_cash: Decimal | None
    payment_date: date | None
    isin: str | None
    related_to: str | None
    raw: dict[str, Any]


def _encoded_params(**params: Any) -> str:
    payload = json.dumps(params, ensure_ascii=True, separators=(",", ":"))
    return base64.b64encode(payload.encode("ascii")).decode("ascii")


def _get(endpoint: str, **params: Any) -> dict[str, Any]:
    token = _encoded_params(**params)
    url = f"{BASE_URL}/{endpoint}/{token}"
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 BOLSABR/0.1",
            "Accept": "application/json, text/xml, application/xml, */*",
            "Referer": "https://sistemaswebb3-listados.b3.com.br/",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=45.0) as response:  # noqa: S310 - fixed B3 host
            return json.loads(response.read().decode("utf-8-sig"))
    except (HTTPError, URLError, TimeoutError) as exc:
        raise RuntimeError(f"B3 listed-companies request failed: {endpoint}: {exc}") from exc


def _optional_date(value: Any) -> date | None:
    if value in (None, ""):
        return None
    try:
        return parse_date(str(value))
    except ValueError:
        return None


def find_companies(query: str) -> tuple[ListedCompany, ...]:
    data = _get(
        "GetInitialCompanies",
        language="pt-br",
        pageNumber=1,
        pageSize=100,
        company=query,
    )
    results: list[ListedCompany] = []
    for row in data.get("results", []):
        issuing = str(row.get("issuingCompany") or "").strip()
        trading = str(row.get("tradingName") or "").strip()
        if not issuing and not trading:
            continue
        code_cvm_raw = row.get("codeCVM")
        results.append(
            ListedCompany(
                issuing_company=issuing,
                trading_name=trading,
                code_cvm=str(code_cvm_raw).strip() if code_cvm_raw not in (None, "") else None,
                raw=row,
            )
        )
    return tuple(results)


def get_cash_distributions(trading_name: str) -> tuple[CashDistribution, ...]:
    data = _get(
        "GetListedCashDividends",
        tradingName=trading_name,
        language="pt-br",
        pageNumber=1,
        pageSize=99999,
    )
    results: list[CashDistribution] = []
    for row in data.get("results", []):
        action = str(row.get("corporateAction") or "").replace("\n", " ").strip()
        stock_type = str(row.get("typeStock") or "").strip().upper()

        # Field names have evolved across B3 versions; preserve the raw record
        # and accept known variants without fabricating missing information.
        payment_raw = (
            row.get("paymentDate")
            or row.get("datePayment")
            or row.get("dateStartPayment")
            or row.get("startPaymentDate")
        )
        isin_raw = row.get("isinCode") or row.get("isin") or row.get("codeISIN")
        related_raw = row.get("relatedTo") or row.get("relatedToPeriod")

        results.append(
            CashDistribution(
                stock_type=stock_type,
                corporate_action=action,
                approval_date=_optional_date(row.get("dateApproval")),
                last_date_with_rights=_optional_date(row.get("lastDatePriorEx")),
                value_cash=br_decimal(str(row.get("valueCash"))) if row.get("valueCash") not in (None, "") else None,
                payment_date=_optional_date(payment_raw),
                isin=str(isin_raw).strip() if isin_raw not in (None, "") else None,
                related_to=str(related_raw).strip() if related_raw not in (None, "") else None,
                raw=row,
            )
        )
    return tuple(results)


def get_cash_distributions_for_ticker(
    issuing_company: str,
    *,
    stock_type: str | None = None,
) -> tuple[CashDistribution, ...]:
    companies = find_companies(issuing_company)
    exact = next(
        (
            company
            for company in companies
            if company.issuing_company.upper() == issuing_company.upper()
        ),
        companies[0] if companies else None,
    )
    if exact is None:
        raise LookupError(f"B3 listed company not found: {issuing_company}")
    distributions = get_cash_distributions(exact.trading_name)
    if stock_type is None:
        return distributions
    wanted = stock_type.strip().upper()
    return tuple(item for item in distributions if item.stock_type == wanted)
