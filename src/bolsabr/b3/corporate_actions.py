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


def _get(endpoint: str, **params: Any) -> Any:
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


def _stock_type_from_isin(isin: str | None) -> str:
    if not isin:
        return ""
    middle = isin.upper()[6:11]
    if "OR" in middle:
        return "ON"
    if "PR" in middle:
        return "PN"
    return ""


def _cash_distribution_from_supplement(row: dict[str, Any]) -> CashDistribution:
    isin_raw = row.get("isinCode") or row.get("assetIssued")
    isin = str(isin_raw).strip() if isin_raw not in (None, "") else None
    action = str(row.get("label") or "").replace("\n", " ").strip()
    return CashDistribution(
        stock_type=_stock_type_from_isin(isin),
        corporate_action=action,
        approval_date=_optional_date(row.get("approvedOn")),
        last_date_with_rights=_optional_date(row.get("lastDatePrior")),
        value_cash=br_decimal(str(row.get("rate"))) if row.get("rate") not in (None, "") else None,
        payment_date=_optional_date(row.get("paymentDate")),
        isin=isin,
        related_to=(
            str(row.get("relatedTo")).strip()
            if row.get("relatedTo") not in (None, "")
            else None
        ),
        raw=row,
    )


def get_company_supplement(issuing_company: str) -> dict[str, Any]:
    """Fetch B3 supplemental listed-company data keyed by issuing-company root."""
    data = _get(
        "GetListedSupplementCompany",
        issuingCompany=issuing_company.strip().upper(),
        language="pt-br",
    )
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, list):
        if not data:
            raise LookupError(f"B3 supplement returned no company: {issuing_company}")
        data = data[0]
    if not isinstance(data, dict):
        raise TypeError(f"Unexpected B3 supplement payload type: {type(data).__name__}")
    return data


def get_cash_distributions_for_isin(
    issuing_company: str,
    isin: str,
) -> tuple[CashDistribution, ...]:
    """Return authoritative B3 cash distributions for one listed security ISIN."""
    supplement = get_company_supplement(issuing_company)
    wanted = isin.strip().upper()
    results = tuple(
        _cash_distribution_from_supplement(row)
        for row in supplement.get("cashDividends", [])
        if str(row.get("isinCode") or row.get("assetIssued") or "").strip().upper() == wanted
    )
    return results


def _stock_type_from_isin(isin: str | None) -> str:
    if not isin:
        return ""
    middle = isin.upper()[6:11]
    if "OR" in middle:
        return "ON"
    if "PR" in middle:
        return "PN"
    return ""


def _cash_distribution_from_supplement(row: dict[str, Any]) -> CashDistribution:
    isin_raw = row.get("isinCode") or row.get("assetIssued")
    isin = str(isin_raw).strip() if isin_raw not in (None, "") else None
    action = str(row.get("label") or "").replace("\n", " ").strip()
    return CashDistribution(
        stock_type=_stock_type_from_isin(isin),
        corporate_action=action,
        approval_date=_optional_date(row.get("approvedOn")),
        last_date_with_rights=_optional_date(row.get("lastDatePrior")),
        value_cash=br_decimal(str(row.get("rate"))) if row.get("rate") not in (None, "") else None,
        payment_date=_optional_date(row.get("paymentDate")),
        isin=isin,
        related_to=(
            str(row.get("relatedTo")).strip()
            if row.get("relatedTo") not in (None, "")
            else None
        ),
        raw=row,
    )


def get_company_supplement(issuing_company: str) -> dict[str, Any]:
    data = _get(
        "GetListedSupplementCompany",
        issuingCompany=issuing_company.strip().upper(),
        language="pt-br",
    )
    if isinstance(data, str):
        data = json.loads(data)
    if isinstance(data, list):
        if not data:
            raise LookupError(f"B3 supplement returned no company: {issuing_company}")
        data = data[0]
    if not isinstance(data, dict):
        raise TypeError(f"Unexpected B3 supplement payload type: {type(data).__name__}")
    return data


def get_cash_distributions_for_isin(
    issuing_company: str,
    isin: str,
) -> tuple[CashDistribution, ...]:
    supplement = get_company_supplement(issuing_company)
    wanted = isin.strip().upper()
    return tuple(
        _cash_distribution_from_supplement(row)
        for row in supplement.get("cashDividends", [])
        if str(row.get("isinCode") or row.get("assetIssued") or "").strip().upper() == wanted
    )


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
