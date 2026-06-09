import { lazy } from 'react';
import { Navigate, type RouteObject } from 'react-router-dom';

import { AdminProvider } from '@/state';
import { paths } from '@/routes/paths';

// The layout is a named export; lazy() needs a default-shaped module.
const AppLayout = lazy(() =>
  import('@/layout/AppLayout').then((m) => ({ default: m.AppLayout })),
);
const ChartPage = lazy(() => import('@/pages/ChartPage'));

export const adminRoutes: RouteObject[] = [
  {
    // AdminProvider scoped here so its boot load (getSource/getBboxes/getGlyphs,
    // which can hit a Cloud Run cold start) only runs for admin routes — the
    // public pages stay fully client-side.
    path: paths.admin.root,
    element: (
      <AdminProvider>
        <AppLayout />
      </AdminProvider>
    ),
    children: [
      { index: true, element: <Navigate to={paths.admin.chart} replace /> },
      { path: 'chart', element: <ChartPage /> },
      // Legacy editor deep-links land back on the chart; editing is now wholly
      // in the Einrichtungs-Wizard / Diagnose modals (opened from the toolbar).
      { path: 'edit/:glyphKey', element: <Navigate to={paths.admin.chart} replace /> },
    ],
  },
];
