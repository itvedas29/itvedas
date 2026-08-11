"""Shared IndexNow submission helper for all ITVedas brain scripts.

IndexNow (https://www.indexnow.org) lets a site push URLs to participating
search engines (Bing, Yandex, Seznam, Naver — Google has no public
instant-indexing API for ordinary sites, so this doesn't cover Google)
the moment they're published or changed, instead of waiting on the next
crawl. KEY is not a secret: it's a public ownership-verification token
whose only job is to be readable at https://itvedas.com/<KEY>.txt (that
file lives at the repo root), so it's fine to commit as a plain constant.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
from typing import Callable

KEY = "f02766f2e63a8a1b0fa5d8c46b7451a3"
ENDPOINT = "https://api.indexnow.org/indexnow"
SITE_HOST = "www.itvedas.com"
SITE_URL = "https://www.itvedas.com"


def submit(paths: list[str], log_fn: Callable[[str], None] | None = None) -> None:
    """Submit one or more site-relative paths (e.g. "/news/foo.html") to
    IndexNow. Best-effort and silent on failure — this must never block
    publishing just because the indexing ping didn't go through.
    """
    if not paths:
        return
    urls = [f"{SITE_URL}{p}" for p in paths]
    payload = {"host": SITE_HOST, "key": KEY, "urlList": urls}
    request = urllib.request.Request(
        ENDPOINT,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            status = response.status
    except urllib.error.HTTPError as e:
        status = e.code
    except Exception as e:
        if log_fn:
            log_fn(f"IndexNow submit failed: {e}")
        return
    if log_fn:
        log_fn(f"IndexNow submit ({len(urls)} url(s)): HTTP {status}")
