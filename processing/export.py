"""Export (C4): the ONLY place that flips FITS (south-up rows) to web (north-up, top row first)."""
import json
from pathlib import Path

import numpy as np
from astropy.time import Time
from PIL import Image, ImageDraw

from .bands import lam_range
from .config import CFG

SCALE = 6          # preview upscale (nearest neighbour, D7)


def to_web(a):
    return np.ascontiguousarray(a[::-1])


def web_px(fits_xy, ny):
    x, y = fits_xy
    return [round(x, 2), round(ny - 1 - y, 2)]


def sequence_stretch(frames):
    p0, p1 = CFG["stretch"]["percentiles"]
    allv = np.concatenate([f["flux"][np.isfinite(f["flux"])] for f in frames])
    return float(np.percentile(allv, p0)), float(np.percentile(allv, p1)), CFG["stretch"]["a"]


def asinh_u8(a, vmin, vmax, aa):
    x = np.clip((a - vmin) / (vmax - vmin), 0, 1)
    y = np.arcsinh(x / aa) / np.arcsinh(1 / aa)
    return np.where(np.isfinite(a), y * 255, 0).astype(np.uint8)


def diverging_rgb(d, lim=10.0):
    t = np.clip(np.nan_to_num(d) / lim, -1, 1)
    r = np.where(t > 0, 1, 1 + t); b = np.where(t < 0, 1, 1 - t); g = 1 - np.abs(t)
    rgb = (np.stack([r, g, b], -1) * 255).astype(np.uint8)
    rgb[~np.isfinite(d)] = (60, 60, 60)
    return rgb


def _big(img):
    return img.resize((img.width * SCALE, img.height * SCALE), Image.NEAREST)


def _cross(draw, x, y, color=(0, 255, 120)):
    X, Y = (x + 0.5) * SCALE, (y + 0.5) * SCALE
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        draw.line([X + dx * 6, Y + dy * 6, X + dx * 18, Y + dy * 18], fill=color, width=2)


def export_bundle(out_dir, target, band, grid_wcs, shape, frames, changes, source, warnings_):
    out = Path(out_dir); out.mkdir(parents=True, exist_ok=True)
    ny, nx = shape
    vmin, vmax, aa = sequence_stretch(frames)
    man_frames, track, gif = [], [], []
    for f in frames:
        e = f["epoch"]
        to_web(f["flux"]).astype("<f4").tofile(out / f"e{e}.f32")
        to_web(f["err"]).astype("<f4").tofile(out / f"e{e}_err.f32")
        u8 = to_web(asinh_u8(f["flux"], vmin, vmax, aa))
        Image.fromarray(u8).save(out / f"e{e}.png")
        m = np.zeros((ny, nx, 4), np.uint8); m[to_web(f["sat"])] = (255, 80, 0, 140)
        Image.fromarray(m, "RGBA").save(out / f"e{e}_mask.png")
        tpx = web_px(f["target_fits_px"], ny)
        date = Time(f["mjd"], format="mjd").datetime.strftime("%b %Y")
        man_frames.append({"epoch": e, "label": date, "mjd": round(f["mjd"], 4),
                           "date": Time(f["mjd"], format="mjd").iso[:10],
                           "n_exposures": f["n_exposures"], "detectors": f["dets"],
                           "f32": f"e{e}.f32", "err_f32": f"e{e}_err.f32", "png": f"e{e}.png",
                           "mask_png": f"e{e}_mask.png", "target_px": tpx,
                           "target_radec": [round(v, 6) for v in f["target_radec"]],
                           "saturated_at_target": bool(f["sat"][int(round(f["target_fits_px"][1])) % ny,
                                                              int(round(f["target_fits_px"][0])) % nx])})
        track.append({"mjd": round(f["mjd"], 4), "x": tpx[0], "y": tpx[1]})
        g = _big(Image.fromarray(u8).convert("RGB")); dr = ImageDraw.Draw(g)
        _cross(dr, *tpx); dr.text((6, 6), f"{target['name']}  {band}  {date}", fill=(255, 255, 0))
        gif.append(g)
    gif[0].save(out / "blink.gif", save_all=True, append_images=gif[1:], duration=600, loop=0)

    man_diffs, strip = [], []
    for c in changes:
        name = f"diff_{c['to']}_{c['from']}"
        to_web(c["diff"]).astype("<f4").tofile(out / f"{name}.f32")
        rgb = to_web(diverging_rgb(c["diff"]))
        Image.fromarray(rgb).save(out / f"{name}.png")
        cands = [dict(cc, y=ny - 1 - cc["y"]) for cc in c["candidates"]]
        man_diffs.append({"from": c["from"], "to": c["to"], "f32": f"{name}.f32", "png": f"{name}.png",
                          "units": "sigma", "candidates": cands})
        if c["from"] == 0:
            g = _big(Image.fromarray(rgb)); dr = ImageDraw.Draw(g)
            for cc in cands[:8]:
                X, Y = (cc["x"] + .5) * SCALE, (cc["y"] + .5) * SCALE
                dr.ellipse([X - 14, Y - 14, X + 14, Y + 14], outline=(0, 0, 0), width=2)
            dr.text((6, 6), f"epoch {c['to']} - epoch 0 (sigma)", fill=(0, 0, 0))
            strip.append(g)
    if strip:
        W = Image.new("RGB", (sum(s.width for s in strip), strip[0].height))
        x = 0
        for s in strip:
            W.paste(s, (x, 0)); x += s.width
        W.save(out / "changes.png")

    h = grid_wcs.to_header()
    manifest = {
        "target_id": target["id"], "name": target["name"], "band": band,
        "lam_range_um": lam_range(band), "source": source,
        "grid": {"nx": nx, "ny": ny, "pix_arcsec": CFG["grid"]["pix_arcsec"], "origin": "top-left, north up",
                 "wcs": {"ctype": [h["CTYPE1"], h["CTYPE2"]], "crval": [h["CRVAL1"], h["CRVAL2"]],
                         "crpix": [h["CRPIX1"], ny + 1 - h["CRPIX2"]], "cdelt": [h["CDELT1"], -h["CDELT2"]]}},
        "units": "MJy/sr (zodi- and background-subtracted)",
        "stretch": {"method": "asinh", "a": aa, "vmin": round(vmin, 5), "vmax": round(vmax, 5), "scope": "sequence"},
        "frames": man_frames, "diffs": man_diffs, "target_track": track,
        "previews": {"blink_gif": "blink.gif", "changes_png": "changes.png" if strip else None},
        "warnings": warnings_,
    }
    (out / "manifest.json").write_text(json.dumps(manifest, indent=1))
    return manifest
