// InfoHint — the one unobtrusive info affordance (a Kurrent "i" that lifts to
// viridian on hover/focus and reveals its detail in a popover on click).
// The popover is click/portal-driven, so a static card shows the mark IN
// CONTEXT — beside the labels it annotates — which is how it actually appears.
// GLKurrent (the cursive "i") is shipped in the global stylesheet, so the mark
// renders as the brand monogram here without any per-preview font wiring.
import { InfoHint } from 'kurrentschrift-app';

import { garamond, paper } from '../../app/src/styles/paper';

const Row = ({ label, children }: { label: string; children: React.ReactNode }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: 6, fontFamily: garamond, color: paper.ink, fontSize: '1.05rem' }}>
    <span>{label}</span>
    {children}
  </div>
);

export const InSettings = () => (
  <div
    style={{
      background: paper.bg,
      border: `1px solid ${paper.line}`,
      borderRadius: 8,
      padding: '20px 24px',
      display: 'flex',
      flexDirection: 'column',
      gap: 14,
      maxWidth: 360,
    }}
  >
    <Row label="Lineatur">
      <InfoHint title="Lineatur">
        Die vier Hilfslinien — Grundlinie, Mittellinie, Ober- und Unterlinie — geben jeder Zone des Buchstabens
        ihren Platz.
      </InfoHint>
    </Row>
    <Row label="Schräglage">
      <InfoHint title="Schräglage">90° steht für eine aufrechte Feder; kleinere Winkel neigen die Schrift nach rechts.</InfoHint>
    </Row>
    <Row label="Schwellzug">
      <InfoHint title="Schwellzug">Die Strichbreite folgt dem Federdruck — Abstriche schwellen an, Aufstriche bleiben Haarlinien.</InfoHint>
    </Row>
  </div>
);

export const Inline = () => (
  <div style={{ fontFamily: garamond, color: paper.ink, fontSize: '1.1rem', maxWidth: 340 }}>
    Diese Vorlage stammt aus dem Jahr 1922{' '}
    <InfoHint>Sütterlins Ausgangsschrift, wie sie an preußischen Schulen gelehrt wurde.</InfoHint>
  </div>
);
