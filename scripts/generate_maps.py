#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import shutil
import subprocess
import tempfile
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from xml.etree import ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
SOURCE_SVG = REPO_ROOT / "media/source/Mapa_do_Brasil_por_codigo_DDD.svg"
STATE_OUTLINE_SOURCE_SVG = REPO_ROOT / "media/source/Blank_Map_of_Brazil.svg"
CN_CSV = REPO_ROOT / "data/raw/Codigos_Nacionais.csv"
BLANK_SVG = REPO_ROOT / "media/blank/brazil_blank_municipal_map.svg"
BLANK_PNG = REPO_ROOT / "media/raster/brazil_blank_municipal_map.png"
STATE_OUTLINE_SVG = REPO_ROOT / "media/blank/brazil_state_outline_map.svg"
STATE_OUTLINE_PNG = REPO_ROOT / "media/raster/brazil_state_outline_map.png"
LOCATOR_PNG_DIR = REPO_ROOT / "media/raster/locator"
LOCATOR_SVG_DIR = REPO_ROOT / "media/locator/svg"
DDD_SUMMARY_CSV = REPO_ROOT / "data/raw/ddd_codes.csv"

SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

NEUTRAL_FILL = "#f4f1e9"
HIGHLIGHT_FILL = "#356d2e"
MUNICIPAL_STROKE = "#ffffff"
OUTLINE_STROKE = "#666666"
MUNICIPAL_STROKE_WIDTH = "0.25"
OUTLINE_STROKE_WIDTH = "0.6"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--png-width", type=int, default=1200)
    parser.add_argument("--write-svg-locators", action="store_true")
    return parser.parse_args()


def local_name(tag: str) -> str:
    return tag.split("}", 1)[1] if "}" in tag else tag


def decode_illustrator_id(value: str | None) -> str:
    return (
        value or ""
    ).replace("_x31_", "1").replace("_x32_", "2").replace("_x33_", "3").replace(
        "_x34_", "4"
    ).replace("_x35_", "5").replace("_x36_", "6").replace("_x37_", "7").replace(
        "_x38_", "8"
    ).replace("_x39_", "9").replace("_x30_", "0")


def read_cn_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle, delimiter=";"))


def build_cn_lookup(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    out: dict[str, dict[str, str]] = {}
    for row in rows:
        municipality_code = (row.get("CO_MUNICIPIO") or "").strip()
        if not municipality_code or (row.get("VIGENTE") or "").strip().lower() != "sim":
            continue
        out[municipality_code] = row
    return out


def municipal_elements(root: ET.Element, municipalities: dict[str, dict[str, str]]) -> list[ET.Element]:
    out: list[ET.Element] = []
    for element in root.iter():
        if local_name(element.tag) not in {"path", "polygon"}:
            continue
        municipality_code = decode_illustrator_id(element.get("id"))
        if municipality_code in municipalities:
            out.append(element)
    return out


def svg_municipality_codes(root: ET.Element) -> set[str]:
    codes: set[str] = set()
    for element in root.iter():
        if local_name(element.tag) not in {"path", "polygon"}:
            continue
        municipality_code = decode_illustrator_id(element.get("id"))
        if municipality_code.isdigit() and len(municipality_code) == 7:
            codes.add(municipality_code)
    return codes


def strip_text_nodes(root: ET.Element) -> None:
    for parent in list(root.iter()):
        for child in list(parent):
            if local_name(child.tag) == "text":
                parent.remove(child)


def reset_title_desc(root: ET.Element, title: str, desc: str) -> None:
    for child in list(root):
        if local_name(child.tag) in {"title", "desc"}:
            root.remove(child)
    title_el = ET.Element(f"{{{SVG_NS}}}title")
    title_el.text = title
    desc_el = ET.Element(f"{{{SVG_NS}}}desc")
    desc_el.text = desc
    root.insert(0, desc_el)
    root.insert(0, title_el)
    root.set("aria-label", title)


def style_root(
    root: ET.Element,
    municipalities: dict[str, dict[str, str]],
    highlighted_cn: str | None,
) -> None:
    strip_text_nodes(root)
    for element in root.iter():
        tag = local_name(element.tag)
        if tag not in {"path", "polygon"}:
            continue
        municipality_code = decode_illustrator_id(element.get("id"))
        if municipality_code in municipalities:
            row = municipalities[municipality_code]
            fill = HIGHLIGHT_FILL if highlighted_cn and row["CN"] == highlighted_cn else NEUTRAL_FILL
            element.set("fill", fill)
            element.set("stroke", MUNICIPAL_STROKE)
            element.set("stroke-width", MUNICIPAL_STROKE_WIDTH)
            continue
        if (element.get("fill") or "").strip().lower() == "none":
            element.set("stroke", OUTLINE_STROKE)
            element.set("stroke-width", OUTLINE_STROKE_WIDTH)


def write_svg(path: Path, root: ET.Element) -> None:
    tree = ET.ElementTree(root)
    path.parent.mkdir(parents=True, exist_ok=True)
    tree.write(path, encoding="utf-8", xml_declaration=True)


def render_png(svg_path: Path, png_path: Path, width: int) -> None:
    if shutil.which("rsvg-convert") is None:
        raise RuntimeError("rsvg-convert is required to render PNG outputs.")
    png_path.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["rsvg-convert", "-w", str(width), str(svg_path)],
        check=True,
        capture_output=True,
    )
    png_path.write_bytes(result.stdout)


def write_blank_assets(
    source_root: ET.Element,
    municipalities: dict[str, dict[str, str]],
    png_width: int,
) -> None:
    blank_root = deepcopy(source_root)
    style_root(blank_root, municipalities, highlighted_cn=None)
    reset_title_desc(blank_root, "Brazil blank DDD base map", "Blank map of Brazil by municipality.")
    write_svg(BLANK_SVG, blank_root)
    render_png(BLANK_SVG, BLANK_PNG, png_width)


def write_state_outline_assets(png_width: int) -> None:
    state_root = ET.parse(STATE_OUTLINE_SOURCE_SVG).getroot()
    strip_text_nodes(state_root)
    for element in state_root.iter():
        if local_name(element.tag) not in {"path", "polygon"}:
            continue
        element.set("fill", NEUTRAL_FILL)
        element.set("stroke", MUNICIPAL_STROKE)
        element.set("stroke-width", "1.5")
    reset_title_desc(
        state_root,
        "Brazil state outline map",
        "Blank map of Brazil showing state outlines only.",
    )
    write_svg(STATE_OUTLINE_SVG, state_root)
    render_png(STATE_OUTLINE_SVG, STATE_OUTLINE_PNG, png_width)


def write_locator_assets(
    source_root: ET.Element,
    municipalities: dict[str, dict[str, str]],
    png_width: int,
    write_svg_locators: bool,
) -> None:
    cn_values = sorted({row["CN"] for row in municipalities.values()}, key=int)
    for cn in cn_values:
        locator_root = deepcopy(source_root)
        style_root(locator_root, municipalities, highlighted_cn=cn)
        reset_title_desc(locator_root, f"Brazil DDD {cn} locator map", f"Locator map highlighting DDD {cn}.")

        if write_svg_locators:
            svg_path = LOCATOR_SVG_DIR / f"ddd_{cn}_locator.svg"
            write_svg(svg_path, locator_root)

        with tempfile.TemporaryDirectory(prefix=f"ddd_{cn}_", dir=REPO_ROOT / "out") as temp_dir:
            temp_svg = Path(temp_dir) / f"ddd_{cn}.svg"
            write_svg(temp_svg, locator_root)
            render_png(temp_svg, LOCATOR_PNG_DIR / f"ddd_{cn}_locator.png", png_width)

        print(f"write media/raster/locator/ddd_{cn}_locator.png")
        if write_svg_locators:
            print(f"write media/locator/svg/ddd_{cn}_locator.svg")


def write_ddd_summary(rows: list[dict[str, str]], missing_geometry_codes: set[str]) -> None:
    by_cn: dict[str, list[dict[str, str]]] = defaultdict(list)
    missing_by_cn: dict[str, int] = defaultdict(int)
    for row in rows:
        if (row.get("VIGENTE") or "").strip().lower() != "sim":
            continue
        cn = (row.get("CN") or "").strip()
        by_cn[cn].append(row)
        if (row.get("CO_MUNICIPIO") or "").strip() in missing_geometry_codes:
            missing_by_cn[cn] += 1

    with DDD_SUMMARY_CSV.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "ddd_code",
                "municipality_count",
                "missing_geometry_municipality_count",
                "states",
                "sample_municipalities",
            ],
        )
        writer.writeheader()
        for cn in sorted((code for code in by_cn if code), key=int):
            cn_rows = by_cn[cn]
            states = sorted({row["SG_UF"] for row in cn_rows if row.get("SG_UF")})
            sample_names = [row["NO_MUNICIPIO"] for row in cn_rows[:5] if row.get("NO_MUNICIPIO")]
            writer.writerow(
                {
                    "ddd_code": cn,
                    "municipality_count": len(cn_rows),
                    "missing_geometry_municipality_count": missing_by_cn.get(cn, 0),
                    "states": "|".join(states),
                    "sample_municipalities": " | ".join(sample_names),
                }
            )


def main() -> int:
    args = parse_args()

    if not SOURCE_SVG.exists():
        raise FileNotFoundError(
            f"Missing source SVG at {SOURCE_SVG}. Run scripts/fetch_map_assets.py first."
        )
    if not STATE_OUTLINE_SOURCE_SVG.exists():
        raise FileNotFoundError(
            "Missing state-outline SVG at "
            f"{STATE_OUTLINE_SOURCE_SVG}. Run scripts/fetch_map_assets.py first."
        )
    if not CN_CSV.exists():
        raise FileNotFoundError(
            f"Missing CN CSV at {CN_CSV}. Run scripts/fetch_reference_data.py first."
        )

    rows = read_cn_rows(CN_CSV)
    municipalities = build_cn_lookup(rows)
    source_root = ET.parse(SOURCE_SVG).getroot()

    svg_codes = svg_municipality_codes(source_root)
    reference_codes = set(municipalities)
    missing_in_svg = reference_codes - svg_codes
    missing_in_reference = svg_codes - reference_codes
    if missing_in_reference:
        preview = ", ".join(sorted(missing_in_reference)[:10])
        raise ValueError(f"SVG municipalities missing from reference data: {preview}")

    write_ddd_summary(rows, missing_in_svg)
    write_blank_assets(source_root, municipalities, args.png_width)
    write_state_outline_assets(args.png_width)
    write_locator_assets(source_root, municipalities, args.png_width, args.write_svg_locators)

    if missing_in_svg:
        preview = ", ".join(
            f"{municipalities[code]['NO_MUNICIPIO']} ({code})" for code in sorted(missing_in_svg)
        )
        print(f"warning: missing geometry for {len(missing_in_svg)} municipality codes: {preview}")

    print(f"write {DDD_SUMMARY_CSV.relative_to(REPO_ROOT)}")
    print(
        "done: "
        f"ddd_codes={len({row['CN'] for row in municipalities.values()})} "
        f"svg_municipalities={len(svg_codes)} "
        f"reference_municipalities={len(municipalities)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
