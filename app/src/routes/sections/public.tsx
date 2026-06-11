import { lazy } from 'react';
import type { RouteObject } from 'react-router-dom';

import { AdminProvider } from '@/context/AdminContext';
import { paths } from '@/routes/paths';

const LandingPage = lazy(() => import('@/pages/LandingPage'));
const WorksheetPage = lazy(() => import('@/pages/WorksheetPage'));
const QuizPage = lazy(() => import('@/pages/QuizPage'));
const ImpressumPage = lazy(() => import('@/pages/ImpressumPage'));
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'));

export const publicRoutes: RouteObject[] = [
  { path: paths.home, element: <LandingPage /> },
  { path: paths.worksheet, element: <WorksheetPage /> },
  { path: paths.impressum, element: <ImpressumPage /> },
  {
    // The quiz reads the source chart + marked bboxes, so it needs the data
    // provider. Scoped to just this route so the other public pages stay
    // client-side and don't pay the boot load / Cloud Run cold start.
    path: paths.quiz,
    element: (
      <AdminProvider>
        <QuizPage />
      </AdminProvider>
    ),
  },
  { path: '*', element: <NotFoundPage /> },
];
