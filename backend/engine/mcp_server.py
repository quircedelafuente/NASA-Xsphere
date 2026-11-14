"""A9 · MCP server: the same engine as tools for Claude (or any MCP client).
Add to Claude Code:  claude mcp add spherex -- python -m engine.mcp_server   (run from backend/, with the requirements installed)"""
from mcp.server.mcpserver import MCPServer   # mcp>=2 (FastMCP was renamed)
from . import config, jobs, resolve as R

mcp = MCPServer('spherex-blink')

def _summary(j):
    if not j:
        return {'status': 'unknown'}
    out = {k: j.get(k) for k in ('status', 'progress', 'message', 'key', 'kind', 'center', 'box', 'visits', 'n_photos_total', 'bands', 'warnings', 'report_url')}
    if j.get('report'):
        r = j['report']
        out['report'] = dict(summary=r['summary'], summary_text=r['summary_text'], checks=r['checks'],
                             sources=[{k: s.get(k) for k in ('id', 'class', 'confidence', 'reason', 'ra_deg', 'dec_deg', 'max_sigma', 'crossmatch')} for s in r['sources'][:40]])
    for b, url in (j.get('bands') or {}).items():
        out.setdefault('bundle_dirs', {})[b] = str(config.CACHE) + url.replace('/manifest.json', '')
    return out

@mcp.tool()
def resolve_object(query: str) -> dict:
    """Turn a star/object name (typos allowed) or coordinates into sky position (RA/Dec, degrees). Known test targets are motion-corrected to 2026."""
    return R.resolve(query)

@mcp.tool()
def list_targets() -> list:
    """The 5 official challenge targets with their catalogue data (position, proper motion, expected motion in pixels/yr)."""
    return config.targets()

@mcp.tool()
def view_sky(query: str = '', ra_deg: float | None = None, dec_deg: float | None = None, bands: list[str] | None = None,
             per_epoch: int | None = None, wait_seconds: int = 900) -> dict:
    """Fetch SPHEREx photos of a spot ON DEMAND (by name or RA/Dec), align them, co-add per visit and compute what changed
    (sigma difference images + change candidates). Returns the bundle folders (C4: manifest.json, frames, diffs). Cached."""
    target = None
    if ra_deg is None or dec_deg is None:
        m = R.resolve(query)['matches']
        if not m:
            return {'status': 'error', 'message': f'Could not resolve "{query}".'}
        ra_deg, dec_deg = m[0]['ra_deg'], m[0]['dec_deg']
        target = next((t for t in config.targets() if t['id'] == m[0].get('id')), None)
    return _summary(jobs.wait(jobs.start_view(ra_deg, dec_deg, bands, per_epoch, target), timeout=wait_seconds))

@mcp.tool()
def scan_zone(ra_deg: float, dec_deg: float, w_arcmin: float = 6.0, h_arcmin: float = 6.0, band: str = 'D4', wait_seconds: int = 1800) -> dict:
    """Autonomous movement check in a zone (max 30′): finds everything that changed between SPHEREx visits, checks each
    against Gaia DR3 and known asteroids, and sorts it (known star, known asteroid, variable, artefact, candidate) with a reason."""
    return _summary(jobs.wait(jobs.start_scan(ra_deg, dec_deg, w_arcmin, h_arcmin, band), timeout=wait_seconds))

@mcp.tool()
def job_status(key: str) -> dict:
    """Progress of a view or scan started earlier."""
    return _summary(jobs.get(key))

if __name__ == '__main__':
    mcp.run()
