#!/usr/bin/env python3
"""Fail if the newest news article is older than MAX_AGE_DAYS.

Run at the end of the Autopilot workflow so a silently broken news pipeline
turns the run red (and GitHub emails the repo owner) instead of going
unnoticed for weeks.
"""
import datetime
import os
import pathlib
import re
import sys

MAX_AGE_DAYS = int(os.environ.get("NEWS_MAX_AGE_DAYS", "3"))
DATE_RE = re.compile(r"^(\d{4}-\d{2}-\d{2})-")


def newest_article_date(news_dir="news"):
    dates = []
    for f in pathlib.Path(news_dir).glob("*.html"):
        m = DATE_RE.match(f.name)
        if m:
            dates.append(datetime.date.fromisoformat(m.group(1)))
    return max(dates) if dates else None


def main():
    newest = newest_article_date()
    today = datetime.datetime.now(datetime.timezone.utc).date()
    if newest is None:
        print("::error::No dated articles found in news/")
        return 1
    age = (today - newest).days
    print(f"Newest news article: {newest} ({age} day(s) old, limit {MAX_AGE_DAYS})")
    if age > MAX_AGE_DAYS:
        print(f"::error::News is stale: last article {newest}. Check the 'Run News Agent' step "
              "(GEMINI_API_KEY / model) in this workflow.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
