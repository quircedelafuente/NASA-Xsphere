"""A9 · MCP server: the same engine as tools for Claude (or any MCP client).
Add to Claude Code:  claude mcp add spherex -- python -m engine.mcp_server   (run from backend/, with the requirements installed)"""
from mcp.server.mcpserver import MCPServer   # mcp>=2 (FastMCP was renamed)
from . import config, jobs, resolve as R

mcp = MCPServer('spherex-blink')

def _summary(j):
    if not j:
        return {'status': 'unknown'}
    out = {k: j.get(k) for k in ('status', 'progress', 'message', 'key', 'center', 'fov_arcmin', 'visits', 'counts', 'n_photos_used', 'n_photos_total', 'stacks_url')}
    sp = j.get('spectrum') or []
    out['spectrum_points'] = len(sp)
    if sp:
        out['spectrum_preview'] = sorted(({'lam_um': p['lam'], 'flux': p['flux'], 'band': p['det'], 'visit': p['ep']} for p in sp), key=lambda p: p['lam_um'])[:60]
    out['stacks_file'] = str(config.CACHE / 'views' / j['key'] / 'stacks.npz') if j.get('key') and j.get('status') == 'done' else None
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
def view_sky(query: str = '', ra_deg: float | None = None, dec_deg: float | None = None, fov_arcmin: float = 3.0,
             bands: list[str] | None = None, per_visit: int = 3, wait_seconds: int = 600) -> dict:
    """Fetch SPHEREx photos of a spot ON DEMAND (by name or RA/Dec), align them and merge per band and visit.
    Returns visits, photos used, spectrum points and the path of the merged float images (stacks.npz, contract I2).
    Cached: a spot already viewed returns instantly. A new spot takes ~1–5 min depending on the network."""
    target = None
    if ra_deg is None or dec_deg is None:
        m = R.resolve(query)['matches']
        if not m:
            return {'status': 'error', 'message': f'Could not resolve "{query}".'}
        ra_deg, dec_deg = m[0]['ra_deg'], m[0]['dec_deg']
        target = next((t for t in config.targets() if t['id'] == m[0].get('id')), None)
    key = jobs.start_view(ra_deg, dec_deg, fov_arcmin, bands or ['D2', 'D4', 'D5', 'D6'], per_visit, target)
    return _summary(jobs.wait(key, timeout=wait_seconds))

@mcp.tool()
def view_status(key: str) -> dict:
    """Progress of a view started earlier (use the key from view_sky)."""
    return _summary(jobs.JOBS.get(key) or jobs.cached(key))

if __name__ == '__main__':
    mcp.run()
