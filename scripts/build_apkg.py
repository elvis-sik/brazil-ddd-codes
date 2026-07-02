#!/usr/bin/env python3
from __future__ import annotations

import csv
import html
from pathlib import Path

import genanki


REPO_ROOT = Path(__file__).resolve().parents[1]
DDD_SUMMARY_CSV = REPO_ROOT / "data/raw/ddd_codes.csv"
OUTPUT_APKG = REPO_ROOT / "out/brazil-ddd-codes.apkg"

BLANK_MAP_FILENAME = "brazil_blank_municipal_map.png"
BLANK_MAP_PATH = REPO_ROOT / "media/raster" / BLANK_MAP_FILENAME
LOCATOR_DIR = REPO_ROOT / "media/raster/locator"

MODEL_ID = 1_893_422_111
DECK_ID = 1_893_422_112


def read_rows(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def split_pipe_values(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def split_sample_municipalities(value: str) -> list[str]:
    return [part.strip() for part in (value or "").split("|") if part.strip()]


def make_map_html(filename: str, alt_text: str, tone: str = "default") -> str:
    frame_class = "map-frame map-frame-hard" if tone == "hard" else "map-frame"
    return (
        f'<div class="{frame_class}">'
        f'<img class="map-image" src="{html.escape(filename)}" alt="{html.escape(alt_text)}">'
        "</div>"
    )


def html_chip_group(title: str, items: list[str], chip_class: str = "") -> str:
    if not items:
        return ""
    chip_attr = f" chip {chip_class}".rstrip()
    chips = "".join(f'<span class="{chip_attr}">{html.escape(item)}</span>' for item in items)
    return (
        '<div class="fact-panel">'
        f'<div class="fact-title">{html.escape(title)}</div>'
        f'<div class="chips">{chips}</div>'
        "</div>"
    )


def html_stat_grid(municipality_count: str, missing_geometry_count: str) -> str:
    stats = [
        ("Municipalities", municipality_count),
        ("Missing Geometry", missing_geometry_count),
    ]
    cells = "".join(
        '<div class="stat-card">'
        f'<div class="stat-label">{html.escape(label)}</div>'
        f'<div class="stat-value">{html.escape(value)}</div>'
        "</div>"
        for label, value in stats
    )
    return f'<div class="stat-grid">{cells}</div>'


def fieldnames() -> list[str]:
    return [
        "ddd_code",
        "states",
        "municipality_count",
        "missing_geometry_municipality_count",
        "sample_municipalities",
        "blank_map",
        "locator_map",
        "Card_BlankMap_HTML",
        "Card_LocatorMap_HTML",
        "Card_States_HTML",
        "Card_SampleMunicipalities_HTML",
        "Card_Stats_HTML",
    ]


def shared_css() -> str:
    return """
:root{
  --paper:#f6efe0;
  --paper-deep:#e6d5b8;
  --ink:#171614;
  --muted:#645b50;
  --forest:#2f5d50;
  --forest-soft:#dce7e2;
  --copper:#a65a34;
  --copper-soft:#f1ddd2;
  --gold:#b48d52;
  --rule:rgba(40,33,24,0.14);
  --shadow:rgba(45,32,17,0.18);
}
.card{
  font-family:"Baskerville","Iowan Old Style","Palatino Linotype","Book Antiqua",serif;
  color:var(--ink);
  background:
    radial-gradient(circle at top left, rgba(180,141,82,0.16), transparent 26%),
    radial-gradient(circle at bottom right, rgba(47,93,80,0.10), transparent 30%),
    linear-gradient(180deg, #fbf6ec 0%, var(--paper) 55%, #ebdec8 100%);
  font-size:20px;
  line-height:1.45;
  padding:22px 18px 30px;
}
.wrap{
  max-width:820px;
  margin:0 auto;
}
.plate{
  position:relative;
  overflow:hidden;
  background:
    linear-gradient(180deg, rgba(255,255,255,0.74), rgba(255,255,255,0.42));
  border:1px solid var(--rule);
  border-radius:28px;
  padding:24px 24px 26px;
  box-shadow:0 18px 46px var(--shadow);
}
.plate::before{
  content:"";
  position:absolute;
  inset:11px;
  border:1px solid rgba(180,141,82,0.22);
  border-radius:20px;
  pointer-events:none;
}
.eyebrow{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  text-transform:uppercase;
  letter-spacing:0.18em;
  font-size:11px;
  color:var(--forest);
  margin:0 0 10px;
}
.title{
  font-size:54px;
  line-height:0.96;
  letter-spacing:-0.04em;
  margin:0;
  color:var(--forest);
}
.subtitle{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  color:var(--muted);
  font-size:18px;
  margin-top:10px;
}
.prompt{
  margin-top:18px;
  padding-top:16px;
  border-top:1px solid var(--rule);
  color:var(--muted);
  font-size:17px;
}
.answer-panel{
  margin-top:18px;
  border-radius:24px;
  border:1px solid rgba(47,93,80,0.16);
  background:
    linear-gradient(180deg, rgba(47,93,80,0.08), rgba(255,255,255,0.72));
  padding:18px 18px 16px;
}
.answer-panel-fixed{
  margin-top:0;
  margin-bottom:18px;
  min-height:112px;
}
.answer-label{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  text-transform:uppercase;
  letter-spacing:0.14em;
  font-size:11px;
  color:var(--copper);
  margin:0 0 8px;
}
.answer-main{
  font-size:38px;
  line-height:1.04;
  margin:0;
  color:var(--forest);
}
.answer-main-slot{
  min-height:40px;
  display:flex;
  align-items:flex-start;
}
.answer-main-placeholder{
  opacity:0;
}
.meta-grid{
  display:grid;
  gap:14px;
  margin-top:18px;
}
@media (min-width:720px){
  .meta-grid{
    grid-template-columns:1fr 1fr;
  }
}
.fact-panel{
  border:1px solid var(--rule);
  border-radius:18px;
  background:rgba(255,255,255,0.58);
  padding:15px 16px 14px;
}
.fact-title,
.stat-label{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:12px;
  text-transform:uppercase;
  letter-spacing:0.12em;
  color:var(--forest);
  margin:0 0 10px;
}
.chips{
  display:flex;
  flex-wrap:wrap;
  gap:10px;
}
.chip{
  display:inline-flex;
  align-items:center;
  border-radius:999px;
  padding:7px 12px;
  background:linear-gradient(180deg, var(--forest-soft), #eff5f3);
  color:var(--forest);
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:14px;
  border:1px solid rgba(47,93,80,0.10);
}
.chip-copper{
  background:linear-gradient(180deg, var(--copper-soft), #f8ece5);
  color:var(--copper);
  border-color:rgba(166,90,52,0.10);
}
.map-frame{
  margin-top:18px;
  border-radius:22px;
  border:1px solid var(--rule);
  background:
    linear-gradient(180deg, rgba(255,255,255,0.84), rgba(243,236,223,0.84));
  padding:16px;
  box-shadow:inset 0 1px 0 rgba(255,255,255,0.48);
}
.map-frame-hard{
  background:
    linear-gradient(180deg, rgba(47,93,80,0.06), rgba(255,255,255,0.76));
}
.map-image{
  display:block;
  width:100%;
  max-width:100%;
  height:auto;
  filter:saturate(0.96) contrast(1.02);
}
.stat-grid{
  display:grid;
  grid-template-columns:repeat(2, minmax(0, 1fr));
  gap:12px;
}
.stat-card{
  border:1px solid var(--rule);
  border-radius:18px;
  padding:14px 15px;
  background:rgba(255,255,255,0.58);
}
.stat-value{
  font-family:"Avenir Next","Gill Sans","Trebuchet MS",sans-serif;
  font-size:24px;
  color:var(--copper);
}
"""


def model() -> genanki.Model:
    return genanki.Model(
        MODEL_ID,
        "Brazil DDD+",
        fields=[{"name": name} for name in fieldnames()],
        templates=[
            {
                "name": "DDD + Blank -> Locator",
                "qfmt": """
<div class="wrap"><div class="plate">
  <div class="eyebrow">Brazilian DDD Code</div>
  <h1 class="title">DDD {{ddd_code}}</h1>
  <div class="subtitle">Start from the municipal blank map, then reveal the highlighted area.</div>
  <div class="prompt">Which part of Brazil does this DDD cover?</div>
  {{Card_BlankMap_HTML}}
</div></div>
""",
                "afmt": """
<div class="wrap"><div class="plate">
  <div class="eyebrow">Brazilian DDD Code</div>
  <h1 class="title">DDD {{ddd_code}}</h1>
  <div class="subtitle">Start from the municipal blank map, then reveal the highlighted area.</div>
  <div class="prompt">Which part of Brazil does this DDD cover?</div>
  {{Card_LocatorMap_HTML}}
</div></div>
<div class="wrap"><div class="answer-panel">
  <div class="answer-label">Locator Details</div>
  <div class="meta-grid">{{Card_States_HTML}}{{Card_Stats_HTML}}</div>
</div></div>
""",
            },
            {
                "name": "Locator -> DDD",
                "qfmt": """
<div class="wrap"><div class="plate">
  <div class="eyebrow">Name The DDD</div>
  <div class="answer-panel answer-panel-fixed">
    <div class="answer-label">Answer</div>
    <div class="answer-main answer-main-slot"><span class="answer-main-placeholder">DDD 99</span></div>
  </div>
  {{Card_LocatorMap_HTML}}
  <div class="prompt">Which Brazilian DDD code is highlighted here?</div>
</div></div>
""",
                "afmt": """
<div class="wrap"><div class="plate">
  <div class="eyebrow">Name The DDD</div>
  <div class="answer-panel answer-panel-fixed">
    <div class="answer-label">Answer</div>
    <div class="answer-main answer-main-slot">DDD {{ddd_code}}</div>
  </div>
  {{Card_LocatorMap_HTML}}
  <div class="prompt">Which Brazilian DDD code is highlighted here?</div>
</div></div>
<div class="wrap"><div class="answer-panel">
  <div class="answer-label">Locator Details</div>
  <div class="meta-grid">{{Card_States_HTML}}{{Card_SampleMunicipalities_HTML}}</div>
</div></div>
""",
            },
        ],
        css=shared_css(),
    )


def note_guid(ddd_code: str) -> str:
    return f"brazil-ddd::{ddd_code}"


def build_note(model: genanki.Model, row: dict[str, str]) -> genanki.Note:
    ddd_code = (row.get("ddd_code") or "").strip()
    states = split_pipe_values(row.get("states") or "")
    municipalities = split_sample_municipalities(row.get("sample_municipalities") or "")

    locator_filename = f"ddd_{ddd_code}_locator.png"
    locator_path = LOCATOR_DIR / locator_filename
    if not locator_path.exists():
        raise FileNotFoundError(
            f"Missing locator image at {locator_path}. Run scripts/generate_maps.py first."
        )

    fields = {
        "ddd_code": ddd_code,
        "states": row.get("states") or "",
        "municipality_count": row.get("municipality_count") or "",
        "missing_geometry_municipality_count": row.get("missing_geometry_municipality_count") or "0",
        "sample_municipalities": row.get("sample_municipalities") or "",
        "blank_map": BLANK_MAP_FILENAME,
        "locator_map": locator_filename,
        "Card_BlankMap_HTML": make_map_html(BLANK_MAP_FILENAME, f"Blank municipal map for DDD {ddd_code}"),
        "Card_LocatorMap_HTML": make_map_html(locator_filename, f"Locator map for DDD {ddd_code}"),
        "Card_States_HTML": html_chip_group("States", states, "chip-copper"),
        "Card_SampleMunicipalities_HTML": html_chip_group("Sample Municipalities", municipalities),
        "Card_Stats_HTML": html_stat_grid(
            row.get("municipality_count") or "",
            row.get("missing_geometry_municipality_count") or "0",
        ),
    }

    return genanki.Note(
        model=model,
        fields=[fields[name] for name in fieldnames()],
        guid=note_guid(ddd_code),
    )


def media_files(rows: list[dict[str, str]]) -> list[str]:
    files = [
        str(BLANK_MAP_PATH),
    ]
    for row in rows:
        ddd_code = (row.get("ddd_code") or "").strip()
        if ddd_code:
            files.append(str(LOCATOR_DIR / f"ddd_{ddd_code}_locator.png"))
    return files


def main() -> int:
    if not DDD_SUMMARY_CSV.exists():
        raise FileNotFoundError(
            f"Missing {DDD_SUMMARY_CSV}. Run scripts/generate_maps.py first."
        )
    if not BLANK_MAP_PATH.exists():
        raise FileNotFoundError(
            "Missing blank deck media. Run scripts/generate_maps.py first."
        )

    rows = read_rows(DDD_SUMMARY_CSV)
    deck = genanki.Deck(DECK_ID, "Brazilian DDD Codes")
    ddd_model = model()

    for row in rows:
        deck.add_note(build_note(ddd_model, row))

    package = genanki.Package(deck)
    package.media_files = media_files(rows)
    OUTPUT_APKG.parent.mkdir(parents=True, exist_ok=True)
    package.write_to_file(str(OUTPUT_APKG))
    print(f"write {OUTPUT_APKG.relative_to(REPO_ROOT)}")
    print(f"done: notes={len(rows)} media_files={len(package.media_files)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
