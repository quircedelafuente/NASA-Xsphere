import { navigate } from '../lib/router';
import { viewUrl } from '../lib/url';
import type { Catalog } from '../lib/useCatalog';
import { KIND_LABEL, TARGET_COPY } from '../copy';

export function TargetChips({ catalog, current, embed, variant = 'cards' }: { catalog: Catalog | null; current?: string; embed?: boolean; variant?: 'cards' | 'pills' }) {
  if (!catalog) return <div className={`chips chips--${variant} chips--loading`} aria-busy="true" />;
  return (
    <ul className={`chips chips--${variant}`}>
      {catalog.index.map((e) => (
        <li key={e.id}>
          <a
            href={viewUrl({ target: e.id }, { embed })}
            className={`chip ${current === e.id ? 'chip--active' : ''}`}
            aria-current={current === e.id ? 'page' : undefined}
            onClick={(ev) => { ev.preventDefault(); navigate(viewUrl({ target: e.id }, { embed })); }}
          >
            <span className="chip__name">{e.name}</span>
            {variant === 'cards' && (
              <>
                <span className="chip__kind">{KIND_LABEL[e.kind]}</span>
                <span className="chip__line">{TARGET_COPY[e.id]?.oneLiner ?? ''}</span>
                <span className="chip__meta mono">{e.n_epochs} visits</span>
              </>
            )}
          </a>
        </li>
      ))}
    </ul>
  );
}
