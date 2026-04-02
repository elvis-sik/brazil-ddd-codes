#!/usr/bin/env python3
from __future__ import annotations

import csv
import urllib.request
from pathlib import Path
from zipfile import ZipFile


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_CSV = REPO_ROOT / "data/raw/reference_data_sources.csv"
ZIP_OUTPUT = REPO_ROOT / "data/raw/pgcn.zip"
EXTRACTED_OUTPUT = REPO_ROOT / "data/raw/Codigos_Nacionais.csv"

USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_0) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def download(url: str, dest: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=180) as response:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(response.read())


def extract_csv(zip_path: Path, output_path: Path) -> None:
    with ZipFile(zip_path) as archive:
        with archive.open("Codigos_Nacionais.csv") as handle:
            output_path.write_bytes(handle.read())


def main() -> int:
    rows = read_rows(SOURCE_CSV)
    if not rows:
        raise ValueError(f"No rows found in {SOURCE_CSV}")

    url = (rows[0].get("download_url") or "").strip()
    if not url:
        raise ValueError(f"Missing download_url in {SOURCE_CSV}")

    if ZIP_OUTPUT.exists() and ZIP_OUTPUT.stat().st_size > 0:
        print(f"skip  {ZIP_OUTPUT.relative_to(REPO_ROOT)}")
    else:
        print(f"fetch {ZIP_OUTPUT.relative_to(REPO_ROOT)}")
        download(url, ZIP_OUTPUT)

    print(f"extract {EXTRACTED_OUTPUT.relative_to(REPO_ROOT)}")
    extract_csv(ZIP_OUTPUT, EXTRACTED_OUTPUT)
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
