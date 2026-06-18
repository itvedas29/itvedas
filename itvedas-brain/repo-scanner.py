#!/usr/bin/env python3
"""Build a machine-readable knowledge map for the ITVedas repository."""

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
from collections import Counter
from typing import Any

DEFAULT_REPOSITORY = "itvedas29/itvedas"
DEFAULT_OUTPUT = pathlib.Path(__file__).resolve().parent / "memory" / "repository.json"
API_ROOT = "https://api.github.com"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan a GitHub repository and write a classified JSON knowledge map."
    )
    parser.add_argument(
        "--repository",
        default=DEFAULT_REPOSITORY,
        help="GitHub repository in owner/name form.",
    )
    parser.add_argument(
        "--ref",
        help="Branch, tag, or commit to scan. Defaults to the repository default branch.",
    )
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help="Destination JSON file.",
    )
    return parser.parse_args()


def github_get(path: str, token: str = "") -> dict[str, Any]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "itvedas-repository-scanner/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    request = urllib.request.Request(f"{API_ROOT}{path}", headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", "replace")
        raise RuntimeError(f"GitHub API returned {error.code}: {detail}") from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach GitHub API: {error.reason}") from error


def classify(path: str) -> list[str]:
    lower = path.lower()
    name = pathlib.PurePosixPath(lower).name
    suffix = pathlib.PurePosixPath(lower).suffix
    categories: list[str] = []

    if lower.startswith("articles/") and suffix == ".html":
        if name == "index.html":
            categories.append("article_indexes")
        else:
            categories.append("articles")

    if lower.startswith("news/") and suffix == ".html":
        categories.append("news_pages")

    if suffix == ".html" and (
        name.startswith("career-") or lower.startswith("career/")
    ):
        categories.append("career_pages")

    if lower.startswith("functions/api/") or "/api/" in lower:
        categories.append("apis")

    if lower.startswith(".github/workflows/") and suffix in {".yml", ".yaml"}:
        categories.append("github_workflows")

    brain_paths = (
        "scripts/brain.py",
        "scripts/news_agent_v2.py",
        "brain/",
        "itvedas-brain/",
    )
    if lower in brain_paths[:2] or lower.startswith(brain_paths[2:]):
        categories.append("brain_logic")

    return categories


def folder_inventory(paths: list[str]) -> list[str]:
    folders: set[str] = set()
    for path in paths:
        parts = pathlib.PurePosixPath(path).parts[:-1]
        for index in range(1, len(parts) + 1):
            folders.add("/".join(parts[:index]))
    return sorted(folders)


def build_snapshot(repository: str, ref: str | None, token: str) -> dict[str, Any]:
    if repository.count("/") != 1:
        raise ValueError("Repository must use owner/name format.")

    owner, name = repository.split("/", 1)
    repo_meta = github_get(
        f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}", token
    )
    resolved_ref = ref or repo_meta["default_branch"]
    encoded_ref = urllib.parse.quote(resolved_ref, safe="")
    tree_data = github_get(
        f"/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(name)}"
        f"/git/trees/{encoded_ref}?recursive=1",
        token,
    )

    if tree_data.get("truncated"):
        raise RuntimeError(
            "GitHub returned a truncated tree; refusing to write incomplete memory."
        )

    files: list[dict[str, Any]] = []
    grouped: dict[str, list[str]] = {
        "articles": [],
        "article_indexes": [],
        "news_pages": [],
        "career_pages": [],
        "apis": [],
        "github_workflows": [],
        "brain_logic": [],
    }

    for item in tree_data.get("tree", []):
        if item.get("type") != "blob":
            continue
        path = item["path"]
        categories = classify(path)
        record = {
            "path": path,
            "size": item.get("size", 0),
            "sha": item.get("sha", ""),
            "categories": categories,
        }
        files.append(record)
        for category in categories:
            grouped[category].append(path)

    files.sort(key=lambda item: item["path"])
    for paths in grouped.values():
        paths.sort()

    file_paths = [item["path"] for item in files]
    extension_counts = Counter(
        pathlib.PurePosixPath(path).suffix.lower() or "[no extension]"
        for path in file_paths
    )

    return {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z"),
        "source": {
            "repository": repository,
            "repository_url": repo_meta.get("html_url"),
            "ref": resolved_ref,
            "tree_sha": tree_data.get("sha"),
            "default_branch": repo_meta.get("default_branch"),
            "visibility": repo_meta.get("visibility"),
            "archived": repo_meta.get("archived", False),
            "pushed_at": repo_meta.get("pushed_at"),
        },
        "summary": {
            "folder_count": len(folder_inventory(file_paths)),
            "file_count": len(files),
            "total_bytes": sum(item["size"] for item in files),
            "extension_counts": dict(sorted(extension_counts.items())),
            "category_counts": {
                category: len(paths) for category, paths in grouped.items()
            },
        },
        "identified": grouped,
        "inventory": {
            "folders": folder_inventory(file_paths),
            "files": files,
        },
    }


def write_json_atomic(output: pathlib.Path, data: dict[str, Any]) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w",
        encoding="utf-8",
        dir=output.parent,
        prefix=f".{output.name}.",
        suffix=".tmp",
        delete=False,
    ) as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write("\n")
        temporary = pathlib.Path(handle.name)
    temporary.replace(output)


def main() -> int:
    args = parse_args()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN", "")
    snapshot = build_snapshot(args.repository, args.ref, token)
    write_json_atomic(args.output, snapshot)

    counts = snapshot["summary"]["category_counts"]
    print(
        f"Scanned {snapshot['summary']['file_count']} files in "
        f"{snapshot['source']['repository']}@{snapshot['source']['ref']}."
    )
    print(
        "Identified "
        + ", ".join(f"{name}={count}" for name, count in counts.items())
        + f". Wrote {args.output}."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
