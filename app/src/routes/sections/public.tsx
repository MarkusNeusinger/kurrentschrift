import { lazy } from 'react';
import { Navigate, type RouteObject } from 'react-router-dom';

import { paths } from '@/routes/paths';

const LandingPage = lazy(() => import('@/pages/LandingPage'));
const SchriftkundePage = lazy(() => import('@/pages/SchriftkundePage'));
const LesenPage = lazy(() => import('@/pages/LesenPage'));
const SchreibenPage = lazy(() => import('@/pages/SchreibenPage'));
const WorksheetPage = lazy(() => import('@/pages/WorksheetPage'));
const ScribePage = lazy(() => import('@/pages/ScribePage'));
const TafelPage = lazy(() => import('@/pages/TafelPage'));
const QuizPage = lazy(() => import('@/pages/QuizPage'));
const ImpressumPage = lazy(() => import('@/pages/ImpressumPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export const publicRoutes: RouteObject[] = [
  { path: paths.home, element: <LandingPage /> },
  // The Schriftkunde's Sütterlin specimen writes live via <WrittenWord>, which
  // fetches from the API on its own (pinned to CONFIG.sourceId) and degrades
  // gracefully — so the page needs no AdminProvider and stays client-side.
  { path: paths.schriftkunde, element: <SchriftkundePage /> },
  // Legacy redirect: this page lived at /lehrbuch before the Schriftkunde rename —
  // forward old links/bookmarks instead of dropping them on the NotFound route.
  { path: '/lehrbuch', element: <Navigate to={paths.schriftkunde} replace /> },
  // Two area hubs group the four tools (Lesen = Quiz + Tafel, Schreiben =
  // Übungsblatt + Federprobe), so the top nav stays at three entries.
  { path: paths.lesen, element: <LesenPage /> },
  { path: paths.schreiben, element: <SchreibenPage /> },
  { path: paths.worksheet, element: <WorksheetPage /> },
  { path: paths.scribe, element: <ScribePage /> },
  { path: paths.impressum, element: <ImpressumPage /> },
  // The writing-chart page (German "Schreibtafel") shows all three Grundtafeln,
  // so it can't ride the single-source AdminProvider: useGrundtafeln fetches the
  // chart sources read-only and groups them by style itself (still pinned to the
  // site-wide source for the one "written" script).
  { path: paths.tafel, element: <TafelPage /> },
  // The quiz fetches its own slim boot data (useQuizSource: source + template
  // summaries + bbox status flags, pinned to the site-wide source) — it no
  // longer mounts the AdminProvider, so it stops downloading the full
  // crop-editing bbox payload just to read the locked/split gating flags.
  { path: paths.quiz, element: <QuizPage /> },
  { path: '*', element: <NotFoundPage /> },
];
