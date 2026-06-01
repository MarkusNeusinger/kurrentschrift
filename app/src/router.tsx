import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ChartPage } from './pages/ChartPage';
import { EditorPage } from './pages/EditorPage';
import { LandingPage } from './pages/LandingPage';
import { WorksheetPage } from './pages/WorksheetPage';

export const router = createBrowserRouter([
  { path: '/', element: <LandingPage /> },
  { path: '/schreiben', element: <WorksheetPage /> },
  {
    path: '/admin',
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/admin/chart" replace /> },
      { path: 'chart', element: <ChartPage /> },
      { path: 'edit/:glyphKey', element: <EditorPage /> },
    ],
  },
  { path: '*', element: <Navigate to="/" replace /> },
]);
