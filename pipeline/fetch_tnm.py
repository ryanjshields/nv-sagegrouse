#!/usr/bin/env python3
"""fetch_tnm.py -- self-contained USGS National Map (TNM) product fetcher.

Queries tnmaccess.nationalmap.gov for a dataset over a bbox, DEDUPLICATES
tiles by most-recent publicationDate (the products API returns multiple
vintages of the same tile; naive use builds a mixed-vintage mosaic), and
emits download URLs on stdout plus a JSON manifest for provenance.

Stdlib only -- runs with any Python 3.8+.

Usage:
  python3 pipeline/fetch_tnm.py \
    --dataset "National Elevation Dataset (NED) 1 arc-second Current" \
    --bbox -120.01,35.0,-114.03,42.01 \
    --manifest data/manifest-3dep-v4.json > data-local/dem/urls.txt
"""
import argparse, json, re, sys, urllib.parse, urllib.request
from datetime import datetime, timezone

BASE = "https://tnmaccess.nationalmap.gov/api/v1/products"

def fetch_page(dataset: str, bbox: str, offset: int, tries: int = 5) -> dict:
    qs = urllib.parse.urlencode({
        "datasets": dataset, "bbox": bbox, "outputFormat": "JSON",
        "max": 100, "offset": offset,
    })
    for i in range(tries):
        try:
            with urllib.request.urlopen(f"{BASE}?{qs}", timeout=60) as r:
                return json.load(r)
        except Exception as e:
            if i == tries - 1:
                raise
            print(f"TNM retry {i+1} after {e}", file=sys.stderr)
            import time; time.sleep(20 * (i + 1))

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--bbox", required=True, help="west,south,east,north (lon/lat)")
    ap.add_argument("--manifest", default="data/manifest-tnm.json")
    args = ap.parse_args()

    items, offset, total = [], 0, None
    while total is None or offset < total:
        page = fetch_page(args.dataset, args.bbox, offset)
        if "items" not in page:
            sys.exit(f"TNM API returned no items -- response: {json.dumps(page)[:400]}")
        items.extend(page["items"])
        total = page.get("total", len(items))
        if not page["items"]:
            break
        offset += len(page["items"])

    # Dedup: the same 1x1-degree cell appears under several vintages AND formats
    # (GeoTIFF/IMG/ArcGrid, dates as YYYY-MM-DD or YYYYMMDD). Group by the cell
    # token (e.g. n36w115); prefer current-format TIFF, then newest publicationDate.
    def cell_key(it):
        m = re.search(r"[ns]\d{2}[ew]\d{3}", (it.get("title", "") + " " + (it.get("downloadURL") or "")), re.I)
        return m.group(0).lower() if m else re.sub(r"\d{8}|\d{4}-\d{2}-\d{2}", "", it.get("title", "")).strip()

    def preference(it):
        url = (it.get("downloadURL") or "").lower()
        return (url.endswith(".tif") or "/tiff/" in url, it.get("publicationDate", ""))

    by_tile = {}
    for it in items:
        key = cell_key(it)
        if key not in by_tile or preference(it) > preference(by_tile[key]):
            by_tile[key] = it
    winners = sorted(by_tile.values(), key=lambda w: w.get("title", ""))

    manifest = {
        "fetched": datetime.now(timezone.utc).isoformat(),
        "dataset": args.dataset,
        "bbox": args.bbox,
        "tile_count": len(winners),
        "raw_product_count": len(items),
        "tiles": [
            {"title": w.get("title"), "url": w.get("downloadURL"),
             "publicationDate": w.get("publicationDate"), "bytes": w.get("sizeInBytes")}
            for w in winners
        ],
    }
    with open(args.manifest, "w") as f:
        json.dump(manifest, f, indent=2)
    for w in winners:
        print(w.get("downloadURL"))
    print(f"{len(winners)} tiles (deduped from {len(items)} products) -> {args.manifest}", file=sys.stderr)

if __name__ == "__main__":
    main()
