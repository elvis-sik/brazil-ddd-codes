#!/usr/bin/env python3
from __future__ import annotations

import csv
import time
import urllib.error
import urllib.request
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = REPO_ROOT / "data/raw/map_asset_sources.csv"
DEST_BY_ASSET_ID = {
    "ddd_brazil_map_commons": REPO_ROOT / "media/source/Mapa_do_Brasil_por_codigo_DDD.svg",
    "blank_brazil_states_commons": REPO_ROOT / "media/source/Blank_Map_of_Brazil.svg",
}

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)
MAX_ATTEMPTS = 6
RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def retry_delay(exc: urllib.error.HTTPError, attempt: int) -> float:
    retry_after = exc.headers.get("Retry-After")
    if retry_after:
        try:
            return min(float(retry_after), 120.0)
        except ValueError:
            pass
    return min(120.0, 5.0 * 2 ** (attempt - 1))


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "image/svg+xml,image/*;q=0.9,*/*;q=0.8",
        },
    )
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(request, timeout=180) as response:
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.write_bytes(response.read())
                return
        except urllib.error.HTTPError as exc:
            if exc.code not in RETRYABLE_STATUS_CODES or attempt == MAX_ATTEMPTS:
                raise
            delay = retry_delay(exc, attempt)
            print(f"retry {attempt}/{MAX_ATTEMPTS} after HTTP {exc.code}: waiting {delay:.0f}s")
            time.sleep(delay)
        except urllib.error.URLError:
            if attempt == MAX_ATTEMPTS:
                raise
            delay = min(120.0, 5.0 * 2 ** (attempt - 1))
            print(f"retry {attempt}/{MAX_ATTEMPTS} after network error: waiting {delay:.0f}s")
            time.sleep(delay)


def main() -> int:
    rows = read_rows(SOURCE_CSV)
    downloaded = 0
    skipped = 0

    for row in rows:
        asset_id = (row.get("asset_id") or "").strip()
        url = (row.get("download_url") or "").strip()
        dest = DEST_BY_ASSET_ID.get(asset_id)
        if not asset_id or not url or dest is None:
            continue
        if dest.exists() and dest.stat().st_size > 0:
            skipped += 1
            print(f"skip  {dest.relative_to(REPO_ROOT)}")
            continue
        print(f"fetch {dest.relative_to(REPO_ROOT)}")
        download(url, dest)
        downloaded += 1

    print(f"done: downloaded={downloaded} skipped={skipped}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
