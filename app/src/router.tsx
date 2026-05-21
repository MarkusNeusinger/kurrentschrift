import { createBrowserRouter, Navigate } from 'react-router-dom';
import { AppLayout } from './layout/AppLayout';
import { ChartPage } from './pages/ChartPage';
import { EditorPage } from './pages/EditorPage';

export const router = createBrowserRouter([
  {
    path: '/',
    element: <AppLayout />,
    children: [
      { index: true, element: <ChartPage /> },
      { path: 'edit/:glyphKey', element: <EditorPage /> },
      { path: '*', element: <Navigate to="/" replace /> },
    ],
  },
]);
