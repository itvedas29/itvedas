#!/usr/bin/env python3
"""Phase 6 - Analytics Agent.

Connects to the Google Analytics 4 Data API, pulls top pages, page
views, sessions, engagement, and conversion pages for the ITVedas
property, and writes memory/analytics.json. decision-engine.py reads
that file to fold real visitor demand into its scoring.

Credentials
-----------
Reading GA4 data requires an OAuth2 access token (the client-side
`GA4_ID` measurement ID used by gtag.js is unrelated and cannot read
data back out). Provide one of:

  GA4_ACCESS_TOKEN       A short-lived OAuth2 bearer token for an
                          identity with "Viewer" access on the GA4
                          property (e.g. minted by
                          google-github-actions/auth in CI, or via
                          `gcloud auth print-access-token` locally).
  GA4_ACCESS_TOKEN_FILE   Path to a file containing that token.

and:

  GA4_PROPERTY_ID         The numeric GA4 property id (not the
                           "G-XXXXXXXXXX" measurement id).

If either is missing, the script writes memory/analytics.json with
status "not_configured" and zeroed metrics rather than failing, so the
rest of the brain pipeline keeps working without analytics access.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import tempfile
import urllib.error
import urllib.request
from typing import Any

BASE_DIR = pathlib.Path(__file__).resolve().parent
DEFAULT_OUTPUT = BASE_DIR / "memory" / "analytics.json"
DATA_API_ROOT = "https://analyticsdata.googleapis.com/v1beta"
DEFAULT_LOOKBACK_DAYS = 28
TOP_PAGES_LIMIT = 25
CONVERSION_PAGES_LIMIT = 25


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Pull GA4 metrics into memory/analytics.json.")
    parser.add_argument("--output", type=pathlib.Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--property-id", default=os.environ.get("GA4_PROPERTY_ID", ""))
    parser.add_argument("--lookback-days", type=int, default=DEFAULT_LOOKBACK_DAYS)
    return parser.parse_args()


def resolve_access_token() -> str:
    token = os.environ.get("GA4_ACCESS_TOKEN", "").strip()
    if token:
        return token
    token_file = os.environ.get("GA4_ACCESS_TOKEN_FILE", "").strip()
    if token_file and pathlib.Path(token_file).is_file():
        return pathlib.Path(token_file).read_text(encoding="utf-8").strip()
    return ""


def run_report(property_id: str, token: str, body: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{DATA_API_ROOT}/properties/{property_id}:runReport",
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
        raise RuntimeError(f"GA4 Data API returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach the GA4 Data API: {error.reason}") from error


def report_rows(report: dict[str, Any]) -> list[dict[str, list[str]]]:
    rows = []
    for row in report.get("rows", []):
        rows.append(
            {
                "dimensions": [value.get("value", "") for value in row.get("dimensionValues", [])],
                "metrics": [value.get("value", "") for value in row.get("metricValues", [])],
            }
        )
    return rows


def to_number(value: str) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def fetch_top_pages(property_id: str, token: str, date_range: dict[str, str]) -> list[dict[str, Any]]:
    report = run_report(
        property_id,
        token,
        {
            "dateRanges": [date_range],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [
                {"name": "screenPageViews"},
                {"name": "sessions"},
                {"name": "engagementRate"},
            ],
            "orderBys": [{"metric": {"metricName": "screenPageViews"}, "desc": True}],
            "limit": TOP_PAGES_LIMIT,
        },
    )
    pages = []
    for row in report_rows(report):
        path = row["dimensions"][0]
        views, sessions, engagement_rate = (to_number(value) for value in row["metrics"])
        pages.append(
            {
                "path": path,
                "page_views": int(views),
                "sessions": int(sessions),
                "engagement_rate": round(engagement_rate, 4),
            }
        )
    return pages


def fetch_conversion_pages(property_id: str, token: str, date_range: dict[str, str]) -> list[dict[str, Any]]:
    report = run_report(
        property_id,
        token,
        {
            "dateRanges": [date_range],
            "dimensions": [{"name": "pagePath"}],
            "metrics": [{"name": "conversions"}],
            "orderBys": [{"metric": {"metricName": "conversions"}, "desc": True}],
            "limit": CONVERSION_PAGES_LIMIT,
        },
    )
    pages = []
    for row in report_rows(report):
        path = row["dimensions"][0]
        conversions = to_number(row["metrics"][0])
        if conversions <= 0:
            continue
        pages.append({"path": path, "conversions": int(conversions)})
    return pages


def fetch_totals(property_id: str, token: str, date_range: dict[str, str]) -> dict[str, Any]:
    report = run_report(
        property_id,
        token,
        {
            "dateRanges": [date_range],
            "metrics": [
                {"name": "screenPageViews"},
                {"name": "sessions"},
                {"name": "engagedSessions"},
                {"name": "engagementRate"},
                {"name": "averageSessionDuration"},
                {"name": "conversions"},
            ],
        },
    )
    rows = report_rows(report)
    if not rows:
        return {
            "page_views": 0,
            "sessions": 0,
            "engaged_sessions": 0,
            "engagement_rate": 0.0,
            "average_session_duration": 0.0,
            "conversions": 0,
        }
    values = [to_number(value) for value in rows[0]["metrics"]]
    page_views, sessions, engaged_sessions, engagement_rate, avg_duration, conversions = values
    return {
        "page_views": int(page_views),
        "sessions": int(sessions),
        "engaged_sessions": int(engaged_sessions),
        "engagement_rate": round(engagement_rate, 4),
        "average_session_duration": round(avg_duration, 1),
        "conversions": int(conversions),
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
        "property_id": None,
        "date_range": None,
        "totals": {
            "page_views": 0,
            "sessions": 0,
            "engaged_sessions": 0,
            "engagement_rate": 0.0,
            "average_session_duration": 0.0,
            "conversions": 0,
        },
        "top_pages": [],
        "conversion_pages": [],
    }


def main() -> int:
    args = parse_args()
    generated_at = (
        dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    )

    token = resolve_access_token()
    property_id = args.property_id.strip()

    if not token or not property_id:
        missing = []
        if not property_id:
            missing.append("GA4_PROPERTY_ID")
        if not token:
            missing.append("GA4_ACCESS_TOKEN (or GA4_ACCESS_TOKEN_FILE)")
        payload = not_configured_payload(
            generated_at, f"Missing required configuration: {', '.join(missing)}."
        )
        write_json_atomic(args.output, payload)
        print(f"GA4 is not configured ({', '.join(missing)} missing). Wrote placeholder {args.output}.")
        return 0

    today = dt.date.today()
    start = today - dt.timedelta(days=args.lookback_days)
    date_range = {"startDate": start.isoformat(), "endDate": today.isoformat()}

    try:
        top_pages = fetch_top_pages(property_id, token, date_range)
        conversion_pages = fetch_conversion_pages(property_id, token, date_range)
        totals = fetch_totals(property_id, token, date_range)
    except RuntimeError as error:
        payload = not_configured_payload(generated_at, str(error))
        payload["status"] = "error"
        payload["property_id"] = property_id
        write_json_atomic(args.output, payload)
        print(f"GA4 request failed: {error}")
        return 1

    payload = {
        "schema_version": 1,
        "generated_at": generated_at,
        "status": "ok",
        "property_id": property_id,
        "date_range": date_range,
        "totals": totals,
        "top_pages": top_pages,
        "conversion_pages": conversion_pages,
    }
    write_json_atomic(args.output, payload)

    print(
        f"Pulled GA4 metrics for property {property_id}: {len(top_pages)} top page(s), "
        f"{len(conversion_pages)} conversion page(s), {totals['sessions']} sessions."
    )
    print(f"Wrote analytics snapshot to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
