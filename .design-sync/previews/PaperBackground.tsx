// PaperBackground — the shared "aged paper" atmosphere (warm radial gradient +
// grain + inset vignette). Shown with real brand content inside so the ground,
// the display face (Playfair Display) and the body face (EB Garamond) are all
// visible at once; plus the bare ground used as a route loading fallback.
import { PaperBackground } from 'kurrentschrift-app';

import { display, garamond, paper } from '../../app/src/styles/paper';

export const WithContent = () => (
  <PaperBackground minHeight={460}>
    <div style={{ maxWidth: 640, margin: '0 auto', padding: '72px 28px', textAlign: 'center' }}>
      <h1
        style={{
          fontFamily: display,
          fontWeight: 600,
          fontSize: '2.6rem',
          lineHeight: 1.1,
          margin: 0,
          color: paper.ink,
        }}
      >
        Die deutsche Schreibschrift,
        <br />
        <span style={{ fontStyle: 'italic', color: paper.viridian }}>wieder lesbar</span>.
      </h1>
      <p
        style={{
          fontFamily: garamond,
          fontSize: '1.15rem',
          lineHeight: 1.7,
          marginTop: 24,
          color: paper.inkSoft,
        }}
      >
        Kurrent und Sütterlin — Buchstabe für Buchstabe aus historischen Vorlagen abgeleitet und in
        der ursprünglichen Federführung neu geschrieben.
      </p>
    </div>
  </PaperBackground>
);

export const BareGround = () => <PaperBackground minHeight={240} />;
