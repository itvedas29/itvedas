#!/usr/bin/env python3
"""Phase 7 - Search Console Agent.

Connects to the Google Search Console API, pulls query- and page-level
search performance, classifies pages into low-CTR / high-impression /
ranking-opportunity / high-click buckets, and writes
memory/search_console.json. decision-engine.py reads that file to
adjust scoring and emit search-console-specific recommendations.

Credentials
-----------
  GSC_SITE_URL            The property as registered in Search Console,
                           e.g. "https://itvedas.com/" or
                           "sc-domain:itvedas.com".
  GSC_ACCESS_TOKEN         An OAuth2 bearer token for an identity with
                           read access to that property (e.g. minted
                           by google-github-actions/auth in CI, or via
                           `gcloud auth print-access-token` locally).
  GSC_ACCESS_TOKEN_FILE    Path to a file containing that token.

If either the site URL or token is missing, the script writes
memory/search_console.json with status "not_configured" and empty
collections rather than failing, so the rest of the brain pipeline
keeps working without Search Console access.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import tempfile
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "memory" / "search_console.json"
SEARCH_ANALYTICS_API_ROOT = "https://www.googleapis.com/webmasters/v3"
DEFAULT_LOOKBACK_DAYS = 28
ROW_LIMIT = 1000

# Classification thresholds.
LOW_CTR_THRESHOLD = 0.02
HIGH_IMPRESSION_PERCENTILE = 0.75
RANKING_OPPORTUNITY_MIN_POSITION = 8.0
RANKING_OPPORTUNITY_MAX_POSITION = 20.0
HIGH_CLICK_PERCENTILE = 0.75
TOP_LIST_LIMIT = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull Search Console metrics into memory/search_console.json.")
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--site-url", default=os.environ.get("GSC_SITE_URL", ""))
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    return parser.parse_args()


def resolve_access_token() -> str:
    token = os.environ.get("GSC_ACCESS_TOKEN", "").strip()
    if token:
        return token
    token_file = os.environ.get("GSC_ACCESS_TOKEN_FILE", "").strip()
    if token_file and pathlib.Path(token_file).is_file():
        return pathlib.Path(token_file).read_text(encoding="utf-8").strip()
    return ""


def search_analytics_query(site_url: str, token: str, body: dict[str, Any]) -> dict[str, Any]:
    encoded_site = urllib.parse.quote(site_url, safe="")
    request = urllib.request.Request(
        f"{SEARCH_ANALYTICS_API_ROOT}/sites/{encoded_site}/searchAnalytics/query",
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"Search Console API returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach the Search Console API: {error.reason}") from error


def fetch_rows(site_url: str, token: str, dimensions: list[str], date_range: dict[str, str]) -> list[dict[str, Any]]:
    report = search_analytics_query(
        site_url,
        token,
        {
            "startDate": date_range["startDate"],
            "endDate": date_range["endDate"],
            "dimensions": dimensions,
            "rowLimit": ROW_LIMIT,
        },
    )
    rows = []
    for row in report.get("rows", []):
        keys = row.get("keys", [])
        record = dict(zip(dimensions, keys))
        record["clicks"] = int(row.get("clicks", 0))
        record["impressions"] = int(row.get("impressions", 0))
        record["ctr"] = round(row.get("ctr", 0.0), 4)
        record["position"] = round(row.get("position", 0.0), 2)
        rows.append(record)
    return rows


def percentile(values: list[float], fraction: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    index = min(len(ordered) - 1, int(len(ordered) * fraction))
    return ordered[index]


def classify_pages(pages: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    impression_threshold = percentile([page["impressions"] for page in pages], HIGH_IMPRESSION_PERCENTILE)
    click_threshold = percentile([page["clicks"] for page in pages], HIGH_CLICK_PERCENTILE)

    low_ctr_pages = sorted(
        (page for page in pages if page["impressions"] >= impression_threshold and page["ctr"] < LOW_CTR_THRESHOLD and page["impressions"] > 0),
        key=lambda page: page["impressions"],
        reverse=True,
    )
    high_impression_pages = sorted(pages, key=lambda page: page["impressions"], reverse=True)
    high_impression_pages = [page for page in high_impression_pages if page["impressions"] >= impression_threshold]
    ranking_opportunities = sorted(
        (
            page
            for page in pages
            if RANKING_OPPORTUNITY_MIN_POSITION <= page["position"] <= RANKING_OPPORTUNITY_MAX_POSITION
        ),
        key=lambda page: page["impressions"],
        reverse=True,
    )
    high_click_pages = sorted(pages, key=lambda page: page["clicks"], reverse=True)
    high_click_pages = [page for page in high_click_pages if page["clicks"] >= click_threshold and page["clicks"] > 0]

    return {
        "low_ctr_pages": low_ctr_pages[:TOP_LIST_LIMIT],
        "high_impression_pages": high_impression_pages[:TOP_LIST_LIMIT],
        "ranking_opportunities": ranking_opportunities[:TOP_LIST_LIMIT],
        "high_click_pages": high_click_pages[:TOP_LIST_LIMIT],
    }


def aggregate_totals(pages: list[dict[str, Any]]) -> dict[str, Any]:
    total_clicks = sum(page["clicks"] for page in pages)
    total_impressions = sum(page["impressions"] for page in pages)
    weighted_position = (
        sum(page["position"] * page["impressions"] for page in pages) / total_impressions
        if total_impressions
        else 0.0
    )
    return {
        "clicks": total_clicks,
        "impressions": total_impressions,
        "ctr": round(total_clicks / total_impressions, 4) if total_impressions else 0.0,
        "average_position": round(weighted_position, 2),
    }


def write_json_atomic(path: pathlib.Path, payload: dict[str, Any]) -> None:
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=path.parent,
        prefix=f".{path.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
        temporary = pathlib.Path(handle.name)
    temporary.replace(path)


def not_configured_payload(generated_at: str, reason: str) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "not_configured",
        "reason": reason,
        "site_url": None,
        "date_range": None,
        "totals": {"clicks": 0, "impressions": 0, "ctr": 0.0, "average_position": 0.0},
        "queries": [],
        "pages": [],
        "insights": {
            "low_ctr_pages": [],
            "high_impression_pages": [],
            "ranking_opportunities": [],
            "high_click_pages": [],
        },
    }


def main() -> int:
    args = parse_args()
    generated_at = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    token = resolve_access_token()
    site_url = args.site_url.strip()

    if not token or not site_url:
        missing = []
        if not site_url:
            missing.append("GSC_SITE_URL")
        if not token:
            missing.append("GSC_ACCESS_TOKEN (or GSC_ACCESS_TOKEN_FILE)")
        payload = not_configured_payload(
            generated_at, f"Missing required configuration: {', '.join(missing)}."
        )
        write_json_atomic(args.output, payload)
        print(f"Search Console is not configured ({', '.join(missing)} missing). Wrote placeholder {args.output}.")
        return 0

    today = dt.date.today()
    start = today - dt.timedelta(days=args.lookback_days)
    date_range = {"startDate": start.isoformat(), "endDate": today.isoformat()}

    try:
        queries = fetch_rows(site_url, token, ["query", "page"], date_range)
        pages = fetch_rows(site_url, token, ["page"], date_range)
    except RuntimeError as error:
        payload = not_configured_payload(generated_at, str(error))
        payload["status"] = "error"
        payload["site_url"] = site_url
        write_json_atomic(args.output, payload)
        print(f"Search Console request failed: {error}")
        return 1

    insights = classify_pages(pages)
    totals = aggregate_totals(pages)

    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "site_url": site_url,
        "date_range": date_range,
        "totals": totals,
        "queries": queries[:TOP_LIST_LIMIT * 4],
        "pages": pages,
        "insights": insights,
    }
    write_json_atomic(args.output, payload)

    print(
        f"Pulled Search Console data for {site_url}: {len(pages)} page(s), {len(queries)} query row(s). "
        f"Low-CTR={len(insights['low_ctr_pages'])} High-impression={len(insights['high_impression_pages'])} "
        f"Ranking-opportunities={len(insights['ranking_opportunities'])} High-click={len(insights['high_click_pages'])}."
    )
    print(f"Wrote search console snapshot to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
