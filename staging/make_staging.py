"""Builds a single self-contained staging page (all bundle PNGs inlined) for reviewing the processing output.
   venv/bin/python staging/make_staging.py <orient.json> <out.html>"""
import base64, json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
B = ROOT / "web/public/bundles"
orient = json.loads(Path(sys.argv[1]).read_text()) if len(sys.argv) > 1 and Path(sys.argv[1]).exists() else {}
def uri(p): return "data:image/png;base64," + base64.b64encode(p.read_bytes()).decode()
def ctx(tid):
    d = B / tid / "context"
    if not (d / "manifest.json").exists(): return None
    m = json.loads((d / "manifest.json").read_text())
    return {"n": m["grid"]["nx"], "frames": [{"survey": f["survey"], "filter": f["filter"], "year": f["year"], "date": f["date"],
            "px": f["target_px"], "img": uri(d / f["png"])} for f in m["frames"]]}
data = []
for t in json.loads((B / "index.json").read_text()):
    band = t["default_band"] if t["default_band"] in t["bands"] else t["bands"][0]
    d = B / t["id"] / band; m = json.loads((d / "manifest.json").read_text())
    data.append({"id": t["id"], "name": t["name"], "kind": t["kind"], "band": band, "lam": m["lam_range_um"],
        "warnings": m["warnings"], "stretch": m["stretch"], "source": m["source"],
        "frames": [{"label": f["label"], "date": f["date"], "n": f["n_exposures"], "px": f["target_px"],
                    "sat": f["saturated_at_target"], "img": uri(d / f["png"]), "mask": uri(d / f["mask_png"])} for f in m["frames"]],
        "diffs": [{"from": x["from"], "to": x["to"], "img": uri(d / x["png"]), "cands": x["candidates"]} for x in m["diffs"]],
        "orient": orient.get(t["id"]), "ctx": ctx(t["id"])})
html = (Path(__file__).parent / "template.html").read_text().replace("/*__DATA__*/[]", json.dumps(data))
Path(sys.argv[2]).write_text(html)
print("written", sys.argv[2], round(len(html) / 1e6, 2), "MB")
