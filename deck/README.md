# Avia route-pitch deck generator

Generates Avia Solutions bespoke route-forecast pitch decks as `.pptx`, in house style,
from a forecast contract and a sourced evidence pack.

Avia Solutions Limited. All rights reserved.

## What is here

| File | Role |
|---|---|
| `avia_deck.py` | House-style library. Slide types and components; the reusable product. |
| `avia_charts.py` | House-palette charts. Title, unit and period on every figure. |
| `avia_maps.py` | Route, catchment and beyond-market maps on real coastline data (basemap). |
| `avia_images.py` | Wikimedia Commons image fetcher with a licence record per file. Runs on the workstation. |
| `build_ba_sjc.py` | Content script: Project Redwood, British Airways London Heathrow to San Jose. |
| `ba_lhr_sjc_deck_contract.json` | The forecast contract the deck reads. |

## House style

Reverse-engineered from the live China Airlines TPE-SJC deck of August 2026, which is the
current bespoke standard.

- 4:3 page, 10 x 7.5 in
- Navy `021D49` header band, body copy `002060`, orange `FFA800` callout panels,
  teal `145A6E` evidence panels, mid blue `1F6FB2` chart series
- Arial throughout
- Client logo top right, page number bottom right
- Full-bleed photographic section dividers
- Source attribution on every figure and table
- Author and last-modified-by set to "Avia Solutions"; proofing language en-GB, verified on save

## Run

    pip install python-pptx matplotlib pillow basemap basemap-data-hires
    python3 build_ba_sjc.py

The build runs twice: the first pass discovers the section page numbers, the second writes
them into the contents slide.

## Conventions

- Data lives on the workstation, never in this repo. Paths come from config or environment
  variables, never hardcoded.
- Images come from the licensed store built by `avia_images.py`, never fetched at render time.
- `assets/` is gitignored: it holds binary imagery that belongs in the image store.
- Git is the single source of truth. Pull before editing, commit and push after.

## Adding a route

Copy `build_ba_sjc.py`, point it at a new contract, and change the content. Everything in
`avia_deck.py`, `avia_charts.py` and `avia_maps.py` is route-agnostic. The qualitative section
depth is currently hard-coded per route; driving it from the route profile is the next piece
of work.
