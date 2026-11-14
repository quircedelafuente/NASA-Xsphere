import { useState } from 'react';
import { SkyRegionSelector, type SkyRegion } from '../ui/sky-region/SkyRegionSelector';

export function SkyRegionDemo() {
  const [submitted, setSubmitted] = useState<SkyRegion | null>(null);
  const [count, setCount] = useState(0);

  function handleRegionSelected(region: SkyRegion) {
    // BACKEND CONNECTION POINT: replace this demo handler with your API client.
    // Return its Promise so the selector can prevent duplicates and show errors.
    console.info('[sky-region] submitted', JSON.stringify(region));
    setSubmitted(region);
    setCount((value) => value + 1);
  }

  return (
    <main className="demo">
      <header>
        <p className="demo__eyebrow">XSPHERE / REGION SELECTOR</p>
        <h1>Choose your patch of sky.</h1>
        <p>Explore, select a square, then confirm its coordinates.</p>
      </header>
      <SkyRegionSelector onRegionSelected={handleRegionSelected} />
      <section className="demo__payload" aria-labelledby="payload-title">
        <div><h2 id="payload-title">Submitted payload</h2><span>Submissions: <output>{count}</output></span></div>
        <pre aria-live="polite">{submitted ? JSON.stringify(submitted, null, 2) : 'No payload submitted yet.'}</pre>
        <p>Demo callback output · ICRS decimal degrees · Full coordinate precision</p>
      </section>
      <footer>Sky context: DSS2 imagery via <a href="https://aladin.cds.unistra.fr/AladinLite/">CDS Aladin Lite</a>. This map is a coordinate picker, not a SPHEREx image product.</footer>
    </main>
  );
}
