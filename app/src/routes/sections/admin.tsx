import { Navigate, type RouteObject } from 'react-router-dom';

import { AdminProvider } from '@/context/AdminContext';
import { paths } from '@/routes/paths';
// The `lazy()` wrappers live in adminPages.tsx so this file exports route data
// and nothing else — see the comment there.
import {
  AdminLayout,
  EigenhandPage,
  JoinsPage,
  LettersPage,
  StartPage,
  WordsPage,
} from '@/routes/sections/adminPages';

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
      // The entry is the Vorlage picker, not a work surface: everything below
      // belongs to exactly one source and its hand, so that choice comes first.
      { index: true, element: <StartPage /> },
      { path: 'buchstaben', element: <LettersPage /> },
      { path: 'uebergaenge', element: <JoinsPage /> },
      { path: 'woerter', element: <WordsPage /> },
      // Hand-scoped, not Vorlage-scoped: the own-hand Bestand and Bogen printer.
      { path: 'eigenhand', element: <EigenhandPage /> },
      // Retired URLs → the view that absorbed each of them, so older bookmarks,
      // notes and work-item links keep working. The chart editor and the
      // Diagnose modal live inside the Buchstaben view now; the Belege list and
      // the Werkbank spine became the Wörter view; the pair matrix became the
      // Übergänge view.
      { path: 'chart', element: <Navigate to={paths.admin.letters} replace /> },
      { path: 'vergleich', element: <Navigate to={paths.admin.letters} replace /> },
      { path: 'paare', element: <Navigate to={paths.admin.joins} replace /> },
      { path: 'belege', element: <Navigate to={paths.admin.words} replace /> },
      { path: 'werkbank', element: <Navigate to={paths.admin.words} replace /> },
      { path: 'edit/:glyphKey', element: <Navigate to={paths.admin.letters} replace /> },
    ],
  },
];
