# DDD Deck Plan

## Purpose

Build a map-heavy Anki deck for Brazil's DDD telephone area codes with clean, fast-rendering visual assets.

## Asset pipeline goals

1. Preserve the original Commons source URL, author, and license.
2. Inspect the original SVG to determine whether DDD regions are separable as stable vector shapes.
3. Join municipality geometries to official CN data using IBGE municipality codes.
4. Generate a neutral blank Brazil map with no code labels and no category coloring.
5. Generate one locator map per DDD code using a shared visual style.
6. Benchmark derived SVG sizes.
7. If SVG outputs remain too heavy for Anki, export optimized PNGs at a controlled resolution.

## Open technical questions

- Are DDD polygons encoded as separate shapes, or are they flattened into Illustrator-heavy groups?
- Are text labels stored as editable text nodes or converted outlines?
- Can the state and coastline structure be retained while removing label clutter cheaply?
- Do some DDD regions consist of disconnected polygons that need multi-part highlighting?

## Current findings

- The source SVG stores visible DDD labels as actual `text` nodes, so they can be removed cleanly.
- Municipal geometries use Illustrator-escaped IDs that decode to IBGE municipality codes.
- The official Anatel `Codigos_Nacionais.csv` dataset includes `CO_MUNICIPIO` and `CN`, so every DDD region can be generated programmatically.
- Rewriting the full municipal SVG per DDD still produces very large SVG files, so PNG is currently the better default deck format.

## Quality bar

- Every generated map should be reproducible from code.
- Area-code assets should have consistent colors, strokes, and margins.
- Final media should prioritize fast rendering in Anki over purity of format.
- If raster export is needed, it should still look crisp on high-density mobile screens.
