import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ChartPage } from './pages/ChartPage';
import { EditorPage } from './pages/EditorPage';
import { LandingPage } from './pages/LandingPage';
import { WorksheetPage } from './pages/WorksheetPage';
import { AdminProvider } from './state';

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/schreiben', element: <WorksheetPage /> },
  {
    // AdminProvider scoped here so its boot load (getSource/getBboxes/getGlyphs,
    // which can hit a Cloud Run cold start) only runs for admin routes — public
    // pages above stay fully client-side.
    path: '/admin',
    element: (
      <AdminProvider>
        <AppLayout />
      </AdminProvider>
    ),
    children: [
      { index: true, element: <Navigate to="/admin/chart" replace /> },
      { path: 'chart', element: <ChartPage /> },
      { path: 'edit/:glyphKey', element: <EditorPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);
