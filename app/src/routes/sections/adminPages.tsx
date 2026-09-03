// The lazily loaded admin pages and the workbench layout, in their own module
// so that `admin.tsx` stays a route table exporting data alone — a file mixing
// component definitions with a data export cannot take a Fast-Refresh update
// (react-refresh/only-export-components).
import { lazy } from 'react';

// The layout is a named export; lazy() needs a default-shaped module.
export const AdminLayout = lazy(() =>
  import('@/layouts/admin/AdminLayout').then((m) => ({ default: m.AdminLayout })),
);
export const StartPage = lazy(() => import('@/pages/admin/StartPage'));
export const LettersPage = lazy(() => import('@/pages/admin/LettersPage'));
export const JoinsPage = lazy(() => import('@/pages/admin/JoinsPage'));
export const WordsPage = lazy(() => import('@/pages/admin/WordsPage'));
export const EigenhandPage = lazy(() => import('@/pages/admin/EigenhandPage'));
