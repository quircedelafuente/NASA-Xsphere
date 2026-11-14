"""B7 · zone report (I3) + optional one LLM call for the plain-English summary."""
import json, os
from collections import Counter
from datetime import datetime, timezone


def summary_counts(sources):
    c = Counter(s["class"] for s in sources)
    return {"sources": len(sources), "known_star": c["known-star"], "known_asteroid": c["known-asteroid"],
            "variable": c["variable"], "artefact": c["artefact"], "candidate": c["candidate-mover"],
            "unknown_static": c["unknown-static"]}


def template_text(rep):
    s = rep["summary"]
    parts = [f"Zone scanned over {rep['visits']} SPHEREx visits ({rep['first_date']} to {rep['last_date']}) in "
             f"{', '.join(rep['bands'])}: {s['sources']} sources."]
    parts.append(f"{s['known_star']} known stars, {s['known_asteroid']} known asteroids, {s['variable']} variable, "
                 f"{s['artefact']} artefacts or one-off detections, {s['unknown_static']} unidentified static sources.")
    movers = [x for x in rep["sources"] if x.get("motion", {}).get("sig", 0) >= 5 and x["class"] in ("known-star", "candidate-mover")]
    for x in movers[:3]:
        parts.append(f"{x['id']} moves {x['motion']['speed_arcsec_yr']:.1f}″/yr: {x['reason']}")
    if s["candidate"]:
        parts.append(f"{s['candidate']} unknown mover(s) flagged as candidates: look at them by eye before calling them anything else.")
    else:
        parts.append("No unknown movers above the detection threshold.")
    return " ".join(parts)


def llm_text(rep):
    """One call per zone, on the numbers only. Needs ANTHROPIC_API_KEY (server env). Returns None if unavailable."""
    if not os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("DISCOVERY_NO_LLM"):
        return None
    try:
        import anthropic
    except ImportError:
        return None
    slim = {"summary": rep["summary"], "visits": rep["visits"], "bands": rep["bands"],
            "sources": [{k: s.get(k) for k in ("id", "class", "confidence", "reason", "appearance_class")}
                        | {"motion_arcsec_yr": s.get("motion", {}).get("speed_arcsec_yr")} for s in rep["sources"][:40]]}
    try:
        client = anthropic.Anthropic()
        r = client.beta.messages.create(
            model=os.environ.get("DISCOVERY_LLM_MODEL", "claude-opus-5-5"),
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            output_config={"effort": "low"},
            system=("You summarise an automatic scan of a small patch of sky imaged by NASA's SPHEREx telescope at several "
                    "dates. Write one plain-English paragraph (max 120 words) for a curious non-expert. Use only the numbers "
                    "given. Say 'candidate', never 'discovery'. Mention any unknown mover or variable first, then what is known."),
            messages=[{"role": "user", "content": json.dumps(slim)}],
        )
        if r.stop_reason == "refusal":
            return None
        txt = "".join(b.text for b in r.content if b.type == "text").strip()
        return txt or None
    except Exception:
        return None


def build(zone, stk, sources, info):
    rep = {"zone": zone, "generated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "visits": len(stk["mjd"]), "bands": stk["bands"],
           "first_date": stk["meta"]["visits"][0].get("start", ""), "last_date": stk["meta"]["visits"][-1].get("end", ""),
           "summary": summary_counts(sources), "sources": sources, "method": info}
    llm = llm_text(rep)
    rep["summary_text"] = llm or template_text(rep)
    rep["summary_text_source"] = "llm" if llm else "rules template"
    return rep
