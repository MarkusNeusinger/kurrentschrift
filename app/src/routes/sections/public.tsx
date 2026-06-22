import { lazy } from 'react';
import type { RouteObject } from 'react-router-dom';

import { AdminProvider } from '@/context/AdminContext';
import { CONFIG } from '@/global-config';
import { paths } from '@/routes/paths';

const LandingPage = lazy(() => import('@/pages/LandingPage'));
const WorksheetPage = lazy(() => import('@/pages/WorksheetPage'));
const ScribePage = lazy(() => import('@/pages/ScribePage'));
const TafelPage = lazy(() => import('@/pages/TafelPage'));
const QuizPage = lazy(() => import('@/pages/QuizPage'));
const ImpressumPage = lazy(() => import('@/pages/ImpressumPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export const publicRoutes: RouteObject[] = [
  { path: paths.home, element: <LandingPage /> },
  { path: paths.worksheet, element: <WorksheetPage /> },
  { path: paths.scribe, element: <ScribePage /> },
  { path: paths.impressum, element: <ImpressumPage /> },
  {
    // The Schreibtafel reads the source chart + its bboxes/glyph status to know
    // which letters have a traced ductus, so it needs the data provider — pinned
    // to the site-wide source like the quiz, never following the admin switcher.
    path: paths.tafel,
    element: (
      <AdminProvider pinnedSourceId={CONFIG.sourceId}>
        <TafelPage />
      </AdminProvider>
    ),
  },
  {
    // The quiz reads the source chart + marked bboxes, so it needs the data
    // provider. Scoped to just this route so the other public pages stay
    // client-side and don't pay the boot load / Cloud Run cold start. Pinned
    // to the site-wide source so the quiz never follows the admin's switcher.
    path: paths.quiz,
    element: (
      <AdminProvider pinnedSourceId={CONFIG.sourceId}>
        <QuizPage />
      </AdminProvider>
    ),
  },
  { path: '*', element: <NotFoundPage /> },
];
