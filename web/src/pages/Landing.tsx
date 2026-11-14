import { lazy, Suspense, useState } from 'react';
import { SearchBox } from '../ui/components/SearchBox';
import { TargetChips } from '../ui/components/TargetChips';
import { Header, Footer, MockBanner } from '../ui/components/Chrome';
import { useCatalog } from '../ui/lib/useCatalog';
import { navigate } from '../ui/lib/router';
import { viewUrl } from '../ui/lib/url';
import { PRODUCT } from '../ui/copy';

const SkyPicker = lazy(() => import('../ui/components/SkyPicker').then((m) => ({ default: m.SkyPicker })));

export function Landing({ embed }: { embed?: boolean }) {
  const catalog = useCatalog();
  const [tab, setTab] = useState<'targets' | 'sky'>('targets');
  const firstId = catalog?.index[0]?.id;

  return (
    <div className="page page--landing">
      {!embed && <Header />}
      {catalog?.mock && <MockBanner />}
      <main id="main" className="landing">
        <section className="hero">
          <p className="eyebrow">NASA SPHEREx · 102 infrared colours · whole sky every 6 months</p>
          <h1>{PRODUCT.tagline}</h1>
          <p className="lede">{PRODUCT.pitch}</p>
          <SearchBox catalog={catalog} embed={embed} />
          {firstId && (
            <p className="hero__tour">
              New here?{' '}
              <a href={viewUrl({ target: firstId, tour: true })} onClick={(e) => { e.preventDefault(); navigate(viewUrl({ target: firstId, tour: true })); }}>
                Take the 2-minute tour of five objects →
              </a>
            </p>
          )}
        </section>

        <section className="pick" aria-labelledby="pick-h">
          <div className="tabs" role="tablist" aria-label="How to pick a patch of sky">
            <h2 id="pick-h" className="sr-only">Pick a patch of sky</h2>
            <button role="tab" aria-selected={tab === 'targets'} className={tab === 'targets' ? 'is-on' : ''} onClick={() => setTab('targets')}>Demo targets</button>
            <button role="tab" aria-selected={tab === 'sky'} className={tab === 'sky' ? 'is-on' : ''} onClick={() => setTab('sky')}>Click on the sky</button>
          </div>
          {tab === 'targets' ? (
            <TargetChips catalog={catalog} embed={embed} />
          ) : (
            <Suspense fallback={<p className="muted">Loading the sky map…</p>}>
              <SkyPicker catalog={catalog} />
            </Suspense>
          )}
        </section>

        <section className="how" aria-labelledby="how-h">
          <h2 id="how-h">How it works</h2>
          <ol className="how__steps">
            <li><strong>Pick a patch of sky.</strong> A star’s name, coordinates, or a click on the map.</li>
            <li><strong>Watch it blink.</strong> The same patch at each SPHEREx visit, shown one after another.</li>
            <li><strong>Spot what changes.</strong> A jumping dot moved; a pulsing one changed brightness.</li>
          </ol>
          <p className="muted">{PRODUCT.heritage}</p>
        </section>
      </main>
      {!embed && <Footer />}
    </div>
  );
}
