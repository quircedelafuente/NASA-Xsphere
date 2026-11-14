import { navigate } from '../lib/router';
import { PRODUCT } from '../copy';

export function Header({ children }: { children?: React.ReactNode }) {
  return (
    <header className="header">
      <a className="skip" href="#main">Skip to content</a>
      <a href="/" className="brand" onClick={(e) => { e.preventDefault(); navigate('/'); }}>
        <BlinkMark />
        <span>{PRODUCT.name}</span>
      </a>
      <div className="header__slot">{children}</div>
    </header>
  );
}

/** Two offset dots — our own mark (no NASA logos, D15). */
export function BlinkMark() {
  return (
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true" className="mark">
      <circle cx="8" cy="11" r="4" fill="var(--fg-dim)" />
      <circle cx="14" cy="11" r="4" fill="var(--accent)" />
    </svg>
  );
}

export function Footer() {
  return (
    <footer className="footer">
      <p>
        Images: NASA/JPL-Caltech SPHEREx, served by <a href="https://irsa.ipac.caltech.edu/Missions/spherex.html">IRSA</a>.
        Sky map: <a href="https://aladin.cds.unistra.fr/">Aladin Lite (CDS)</a>. Built for the NASA Space Apps Challenge 2026.
        Not an official NASA product.
      </p>
    </footer>
  );
}

export function MockBanner({ compact }: { compact?: boolean }) {
  return (
    <div className={`mock-banner ${compact ? 'mock-banner--compact' : ''}`} role="note">
      {compact ? 'Simulated demo data' : 'Demo data · images are simulated until the real SPHEREx cut-outs are published'}
    </div>
  );
}
