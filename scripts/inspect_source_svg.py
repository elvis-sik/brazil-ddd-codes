#!/usr/bin/env python3
from __future__ import annotations

from collections import Counter
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SVG = REPO_ROOT / "media/source/Mapa_do_Brasil_por_codigo_DDD.svg"


def local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def main() -> int:
    if not SOURCE_SVG.exists():
        raise FileNotFoundError(
            f"Missing source SVG at {SOURCE_SVG}. Run scripts/fetch_map_assets.py first."
        )

    tree = ET.parse(SOURCE_SVG)
    root = tree.getroot()

    tag_counts = Counter(local_name(element.tag) for element in root.iter())
    class_counts = Counter()
    id_counts = Counter()

    for element in root.iter():
        class_name = (element.get("class") or "").strip()
        element_id = (element.get("id") or "").strip()
        if class_name:
            class_counts[class_name] += 1
        if element_id:
            id_counts[element_id.split("_", 1)[0]] += 1

    print(f"file={SOURCE_SVG.relative_to(REPO_ROOT)}")
    print(f"size_bytes={SOURCE_SVG.stat().st_size}")
    print("top_tags=")
    for tag, count in tag_counts.most_common(15):
        print(f"  {tag}: {count}")

    print("top_classes=")
    for class_name, count in class_counts.most_common(15):
        print(f"  {class_name}: {count}")

    print("top_id_prefixes=")
    for prefix, count in id_counts.most_common(15):
        print(f"  {prefix}: {count}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
