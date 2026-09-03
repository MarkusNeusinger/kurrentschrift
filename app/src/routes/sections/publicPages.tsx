// The lazily loaded public pages, in their own module so that `public.tsx` can
// stay what it is: a route table, exporting data and nothing else. A file that
// mixes component definitions with a data export cannot take a Fast-Refresh
// update (react-refresh/only-export-components) — splitting the two costs one
// import and keeps every route a chunk of its own, as before.
import { lazy } from 'react';

export const LandingPage = lazy(() => import('@/pages/LandingPage'));
export const SchriftkundePage = lazy(() => import('@/pages/SchriftkundePage'));
export const LesenPage = lazy(() => import('@/pages/LesenPage'));
export const SchreibenPage = lazy(() => import('@/pages/SchreibenPage'));
export const WorksheetPage = lazy(() => import('@/pages/WorksheetPage'));
export const ScribePage = lazy(() => import('@/pages/ScribePage'));
export const TafelPage = lazy(() => import('@/pages/TafelPage'));
export const QuizPage = lazy(() => import('@/pages/QuizPage'));
export const VergleichenPage = lazy(() => import('@/pages/VergleichenPage'));
export const ImpressumPage = lazy(() => import('@/pages/ImpressumPage'));
