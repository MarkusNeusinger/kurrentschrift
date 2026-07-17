import { lazy } from 'react';
import { Navigate, type RouteObject } from 'react-router-dom';

import { AdminProvider } from '@/context/AdminContext';
import { paths } from '@/routes/paths';

// The layout is a named export; lazy() needs a default-shaped module.
const AdminLayout = lazy(() =>
  import('@/layouts/admin/AdminLayout').then((m) => ({ default: m.AdminLayout })),
);
const ChartPage = lazy(() => import('@/pages/admin/ChartPage'));
const ComparePage = lazy(() => import('@/pages/admin/ComparePage'));
const PairsPage = lazy(() => import('@/pages/admin/PairsPage'));

export const adminRoutes: RouteObject[] = [
  {
    // AdminProvider scoped here so its boot load (getSource/getBboxes/getGlyphs,
    // which can hit a Cloud Run cold start) only runs for admin routes — the
    // public pages stay fully client-side.
    path: paths.admin.root,
    element: (
      <AdminProvider>
        <AdminLayout />
      </AdminProvider>
    ),
    children: [
      { index: true, element: <Navigate to={paths.admin.chart} replace /> },
      { path: 'chart', element: <ChartPage /> },
      { path: 'vergleich', element: <ComparePage /> },
      { path: 'paare', element: <PairsPage /> },
      // Legacy editor deep-links land back on the chart; editing is now wholly
      // in the Einrichtungs-Wizard / Diagnose modals (opened from the toolbar).
      { path: 'edit/:glyphKey', element: <Navigate to={paths.admin.chart} replace /> },
    ],
  },
];
