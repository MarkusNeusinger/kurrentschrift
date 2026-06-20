// BootStatus — the full-page boot screen (loading spinner / load error), in its
// two shells: `plain` (flat centered page) and `paper` (the paper-texture shell
// with top-left error copy). The variant × shell matrix is the whole surface.
import { BootStatus } from 'kurrentschrift-app';

export const Loading = () => <BootStatus variant="loading" message="Vorlage wird geladen …" />;

export const LoadingPaper = () => (
  <BootStatus variant="loading" shell="paper" message="Einen Augenblick — die Schrift wird vorbereitet …" />
);

export const Error = () => (
  <BootStatus
    variant="error"
    title="Verbindung unterbrochen"
    message="Der Server ist gerade nicht erreichbar."
    onRetry={() => {}}
    retryLabel="Erneut versuchen"
  />
);

export const ErrorPaper = () => (
  <BootStatus
    variant="error"
    shell="paper"
    title="Vorlage nicht gefunden"
    message="Diese Schriftvorlage konnte nicht geladen werden."
    detail={
      <>
        Läuft der Entwicklungsserver? Starte ihn mit <code>uv run uvicorn api.main:app</code>.
      </>
    }
    onRetry={() => {}}
    retryLabel="Neu laden"
  />
);
