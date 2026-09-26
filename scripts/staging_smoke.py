from __future__ import annotations

import argparse
import json
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from xml.etree import ElementTree


class CanonicalParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.canonical: str | None = None

    def handle_starttag(
        self,
        tag: str,
        attrs: list[tuple[str, str | None]],
    ) -> None:
        if tag.lower() != "link":
            return
        values = {key.lower(): value for key, value in attrs}
        rel = (values.get("rel") or "").lower().split()
        if "canonical" in rel and values.get("href"):
            self.canonical = values["href"]


def _fetch(
    url: str,
    *,
    timeout: float,
    expected_status: int = 200,
) -> tuple[int, bytes, dict[str, str]]:
    request = Request(
        url,
        headers={
            "User-Agent": "BOLSABR-Staging-Smoke/1.0",
            "Accept": "*/*",
        },
    )
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310
            status = response.status
            body = response.read()
            headers = dict(response.headers.items())
    except HTTPError as exc:
        status = exc.code
        body = exc.read()
        headers = dict(exc.headers.items()) if exc.headers else {}
    except (URLError, TimeoutError) as exc:
        raise RuntimeError(f"request failed for {url}: {exc}") from exc

    if status != expected_status:
        preview = body[:500].decode("utf-8", errors="replace")
        raise AssertionError(
            f"{url} returned HTTP {status}, expected {expected_status}: {preview}"
        )
    return status, body, headers


def _xml_locations(payload: bytes) -> list[str]:
    root = ElementTree.fromstring(payload)
    locations: list[str] = []
    for element in root.iter():
        if element.tag.rsplit("}", 1)[-1] == "loc" and element.text:
            locations.append(element.text.strip())
    return locations


def _canonical(html: bytes) -> str | None:
    parser = CanonicalParser()
    parser.feed(html.decode("utf-8", errors="replace"))
    return parser.canonical


def _path(url: str) -> str:
    return urlparse(url).path.rstrip("/") or "/"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Remote smoke test for a deployed BOLSABR Web environment."
    )
    parser.add_argument("base_url", help="Public Web URL, e.g. https://staging.example.com")
    parser.add_argument(
        "--ticker",
        default="PETR4",
        help="Known published underlying used for deep checks. Default: PETR4.",
    )
    parser.add_argument(
        "--min-assets",
        type=int,
        default=1,
        help="Minimum asset URLs expected in the root sitemap.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=20.0,
        help="Per-request timeout in seconds.",
    )
    parser.add_argument(
        "--require-https",
        action="store_true",
        help="Fail unless the public base URL uses HTTPS.",
    )
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    ticker = args.ticker.strip().upper()
    parsed_base = urlparse(base)
    if parsed_base.scheme not in {"http", "https"} or not parsed_base.netloc:
        raise ValueError(f"invalid base URL: {base!r}")
    if args.require_https and parsed_base.scheme != "https":
        raise AssertionError("staging URL must use HTTPS")
    if args.min_assets < 1:
        raise ValueError("--min-assets must be >= 1")

    report: dict[str, object] = {
        "base_url": base,
        "ticker": ticker,
        "checks": {},
    }
    checks = report["checks"]
    assert isinstance(checks, dict)

    _fetch(f"{base}/healthz", timeout=args.timeout)
    checks["healthz"] = "ok"

    _, root_sitemap, _ = _fetch(
        f"{base}/sitemap.xml",
        timeout=args.timeout,
    )
    root_locations = _xml_locations(root_sitemap)
    asset_locations = [
        location
        for location in root_locations
        if "/acoes/" in urlparse(location).path
        and urlparse(location).path.endswith("/opcoes")
    ]
    if len(asset_locations) < args.min_assets:
        raise AssertionError(
            f"root sitemap has {len(asset_locations)} asset URLs; "
            f"expected at least {args.min_assets}"
        )

    expected_asset_path = f"/acoes/{ticker}/opcoes"
    if not any(_path(location) == expected_asset_path for location in asset_locations):
        raise AssertionError(
            f"{ticker} missing from root sitemap"
        )
    checks["root_sitemap_assets"] = len(asset_locations)

    _, robots_payload, _ = _fetch(
        f"{base}/robots.txt",
        timeout=args.timeout,
    )
    robots = robots_payload.decode("utf-8", errors="replace")
    root_sitemap_url = f"{base}/sitemap.xml"
    option_sitemap_url = f"{base}/opcoes/sitemap/{ticker}.xml"
    if root_sitemap_url not in robots:
        raise AssertionError("robots.txt does not advertise root sitemap")
    if option_sitemap_url not in robots:
        raise AssertionError(
            f"robots.txt does not advertise {ticker} option sitemap"
        )
    checks["robots"] = "ok"

    _, option_sitemap, _ = _fetch(
        option_sitemap_url,
        timeout=args.timeout,
    )
    contract_locations = _xml_locations(option_sitemap)
    if not contract_locations:
        raise AssertionError(
            f"{ticker} option sitemap is empty"
        )
    if len(contract_locations) >= 50_000:
        raise AssertionError(
            f"{ticker} option sitemap reached unsafe URL count: "
            f"{len(contract_locations)}"
        )
    checks["contract_urls"] = len(contract_locations)

    asset_url = f"{base}{expected_asset_path}"
    _, asset_html, _ = _fetch(asset_url, timeout=args.timeout)
    asset_text = asset_html.decode("utf-8", errors="replace")
    if ticker not in asset_text:
        raise AssertionError(f"{ticker} missing from asset page HTML")
    if "EOD" not in asset_text:
        raise AssertionError("asset page does not expose EOD freshness")
    asset_canonical = _canonical(asset_html)
    if asset_canonical != asset_url:
        raise AssertionError(
            f"asset canonical mismatch: {asset_canonical!r} != {asset_url!r}"
        )
    checks["asset_page"] = "ok"

    first_contract_url = contract_locations[0]
    first_contract_parsed = urlparse(first_contract_url)
    if first_contract_parsed.netloc != parsed_base.netloc:
        raise AssertionError(
            f"contract sitemap points to another host: {first_contract_url}"
        )

    _, contract_html, _ = _fetch(
        first_contract_url,
        timeout=args.timeout,
    )
    contract_canonical = _canonical(contract_html)
    if contract_canonical != first_contract_url:
        raise AssertionError(
            "contract canonical mismatch: "
            f"{contract_canonical!r} != {first_contract_url!r}"
        )
    checks["contract_page"] = {
        "url": first_contract_url,
        "canonical": contract_canonical,
    }

    _fetch(
        f"{base}/acoes/ZZZZ99/opcoes",
        timeout=args.timeout,
        expected_status=404,
    )
    checks["unknown_asset_404"] = "ok"

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
