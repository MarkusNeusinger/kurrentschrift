// PublicFooter — the minimal legal footer (a hairline + one centered Impressum
// link). Meant to sit inside the paper ground, so we show it on a paper-toned
// strip rather than a bare white card.
import { PublicFooter } from 'kurrentschrift-app';

import { paper } from '../../app/src/styles/paper';

export const OnPaper = () => (
  <div style={{ background: paper.bg, padding: '40px 0 8px' }}>
    <PublicFooter />
  </div>
);
