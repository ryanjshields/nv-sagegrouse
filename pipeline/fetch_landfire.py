#!/usr/bin/env python3
"""fetch_landfire.py -- fetch a LANDFIRE layer clip via the LANDFIRE Product Service (LFPS v2 API).

Submits an async clip job, polls until done, downloads the zip. Stdlib only.
API: https://lfps.usgs.gov/api/job/submit  (Layer_List, Area_of_Interest, Email required)

Usage:
  python3 pipeline/fetch_landfire.py --layer LF2025_EVT \
    --bbox "-120.01 35.0 -114.03 42.01" --email you@example.com \
    --out data-local/landfire/evt.zip
"""
import argparse, json, sys, time, urllib.parse, urllib.request

BASE = "https://lfps.usgs.gov/api/job"

def get_json(url: str) -> dict:
    with urllib.request.urlopen(url, timeout=120) as r:
        body = r.read().decode()
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        sys.exit(f"non-JSON from {url.split('?')[0]}: {body[:300]}")

def submit(layer: str, bbox: str, email: str) -> dict:
    qs = urllib.parse.urlencode({"Layer_List": layer, "Area_of_Interest": bbox, "Email": email})
    return get_json(f"{BASE}/submit?{qs}")

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--layer", required=True)
    ap.add_argument("--fallback-layer")
    ap.add_argument("--bbox", required=True, help='"west south east north" (lon/lat)')
    ap.add_argument("--email", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--poll-seconds", type=int, default=30)
    args = ap.parse_args()

    job = submit(args.layer, args.bbox, args.email)
    job_id = job.get("jobId") or job.get("JobId") or (job.get("job") or {}).get("jobId")
    if not job_id and args.fallback_layer:
        print(f"submit failed for {args.layer}: {json.dumps(job)[:200]}; trying {args.fallback_layer}", file=sys.stderr)
        job = submit(args.fallback_layer, args.bbox, args.email)
        job_id = job.get("jobId") or job.get("JobId") or (job.get("job") or {}).get("jobId")
    if not job_id:
        sys.exit(f"LFPS submit failed: {json.dumps(job)[:400]}")
    print(f"LFPS job {job_id} submitted", file=sys.stderr)

    dl_url = None
    while True:
        st = get_json(f"{BASE}/status?JobId={urllib.parse.quote(str(job_id))}")
        status = (st.get("status") or st.get("jobStatus") or "").lower()
        if "succe" in status or "complete" in status:
            dl_url = st.get("outputFile") or st.get("downloadUrl") or (st.get("output") or {}).get("url")
            break
        if "fail" in status or "cancel" in status or "error" in status:
            sys.exit(f"LFPS job failed: {json.dumps(st)[:500]}")
        time.sleep(args.poll_seconds)

    if not dl_url:
        sys.exit(f"job done but no download url in status: {json.dumps(st)[:400]}")
    urllib.request.urlretrieve(dl_url, args.out)
    print(f"LANDFIRE_FETCH_COMPLETE {args.out}")

if __name__ == "__main__":
    main()
