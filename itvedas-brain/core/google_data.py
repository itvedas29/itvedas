"""Read-only Google Search Console + GA4 access for the growth agent.

Auth is a Google Cloud service account whose JSON key is supplied in the
GOOGLE_SERVICE_ACCOUNT_JSON secret (raw JSON or base64 of it). The service
account's email must be added as a user on the Search Console property and
as a Viewer on the GA4 property - see docs/GROWTH-AGENT.md.

Only read-only scopes are requested: this module can never change anything
in Search Console or Analytics.
"""
from __future__ import annotations

import base64
import json
import os
import urllib.parse

SCOPES = [
    "https://www.googleapis.com/auth/webmasters.readonly",
    "https://www.googleapis.com/auth/analytics.readonly",
]
GSC_ENDPOINT = "https://searchconsole.googleapis.com/webmasters/v3/sites/{site}/searchAnalytics/query"
GA4_ENDPOINT = "https://analyticsdata.googleapis.com/v1beta/properties/{prop}:runReport"
TIMEOUT = 60


class GoogleDataError(RuntimeError):
    pass


def load_service_account_info(raw: str | None = None) -> dict | None:
    """Parse the service-account key from the environment.

    Accepts raw JSON or base64-encoded JSON. Returns None when unset so the
    caller can skip cleanly; raises GoogleDataError when set but unreadable.
    """
    raw = (raw if raw is not None else os.environ.get("GOOGLE_SERVICE_ACCOUNT_JSON", "")).strip()
    if not raw:
        return None
    if not raw.startswith("{"):
        try:
            raw = base64.b64decode(raw).decode("utf-8")
        except Exception:
            raise GoogleDataError("GOOGLE_SERVICE_ACCOUNT_JSON is neither JSON nor base64 JSON") from None
    try:
        info = json.loads(raw)
    except json.JSONDecodeError:
        raise GoogleDataError("GOOGLE_SERVICE_ACCOUNT_JSON is not valid JSON") from None
    if info.get("type") != "service_account" or not info.get("client_email"):
        raise GoogleDataError("GOOGLE_SERVICE_ACCOUNT_JSON is not a service-account key")
    return info


def make_session(info: dict):
    """Authorized HTTP session. Imported lazily so the rest of the brain (and
    the unit tests) do not need google-auth installed."""
    from google.auth.transport.requests import AuthorizedSession
    from google.oauth2 import service_account

    creds = service_account.Credentials.from_service_account_info(info, scopes=SCOPES)
    return AuthorizedSession(creds)


def _post(session, url: str, body: dict) -> dict:
    response = session.post(url, json=body, timeout=TIMEOUT)
    if response.status_code >= 400:
        # Google's error bodies name the missing permission; keep them short.
        raise GoogleDataError(f"HTTP {response.status_code} from {url.split('?')[0]}: {response.text[:400]}")
    return response.json()


def gsc_find_site(session, domain: str = "itvedas.com") -> str | None:
    """The Search Console property this service account can read for `domain`
    (a Domain property is preferred over URL-prefix ones), or None."""
    response = session.get("https://searchconsole.googleapis.com/webmasters/v3/sites", timeout=TIMEOUT)
    if response.status_code >= 400:
        raise GoogleDataError(f"HTTP {response.status_code} listing Search Console sites: {response.text[:400]}")
    sites = [e.get("siteUrl", "") for e in response.json().get("siteEntry", [])
             if e.get("permissionLevel") != "siteUnverifiedUser"]
    matches = [u for u in sites if domain in u]
    matches.sort(key=lambda u: (not u.startswith("sc-domain:"), "www." not in u, not u.startswith("https")))
    return matches[0] if matches else None


def gsc_query(session, site: str, start: str, end: str, dimensions: list[str],
              row_limit: int = 5000, page_filter: str | None = None) -> list[dict]:
    """Search Analytics rows as dicts: the requested dimensions plus
    clicks, impressions, ctr, position. Dates are YYYY-MM-DD, inclusive."""
    url = GSC_ENDPOINT.format(site=urllib.parse.quote(site, safe=""))
    rows: list[dict] = []
    start_row = 0
    while len(rows) < row_limit:
        body: dict = {
            "startDate": start, "endDate": end, "dimensions": dimensions,
            "type": "web", "rowLimit": min(25000, row_limit - len(rows)), "startRow": start_row,
        }
        if page_filter:
            body["dimensionFilterGroups"] = [{"filters": [
                {"dimension": "page", "operator": "equals", "expression": page_filter}]}]
        batch = _post(session, url, body).get("rows", [])
        for r in batch:
            row = dict(zip(dimensions, r.get("keys", [])))
            row.update(clicks=r.get("clicks", 0), impressions=r.get("impressions", 0),
                       ctr=r.get("ctr", 0.0), position=r.get("position", 0.0))
            rows.append(row)
        if len(batch) < body["rowLimit"]:
            break
        start_row += len(batch)
    return rows


def ga4_report(session, property_id: str, start: str, end: str, dimensions: list[str],
               metrics: list[str], limit: int = 1000) -> list[dict]:
    """GA4 Data API report rows as dicts keyed by dimension/metric name.
    Metric values are returned as floats."""
    prop = str(property_id).replace("properties/", "").strip()
    body = {
        "dateRanges": [{"startDate": start, "endDate": end}],
        "dimensions": [{"name": d} for d in dimensions],
        "metrics": [{"name": m} for m in metrics],
        "limit": limit,
    }
    if metrics:
        body["orderBys"] = [{"metric": {"metricName": metrics[0]}, "desc": True}]
    data = _post(session, GA4_ENDPOINT.format(prop=prop), body)
    out = []
    for r in data.get("rows", []):
        row = {d: v.get("value", "") for d, v in zip(dimensions, r.get("dimensionValues", []))}
        for m, v in zip(metrics, r.get("metricValues", [])):
            try:
                row[m] = float(v.get("value", 0))
            except (TypeError, ValueError):
                row[m] = 0.0
        out.append(row)
    return out
