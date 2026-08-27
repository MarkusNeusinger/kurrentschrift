// Framework-free per-route head management — the planned react-helmet-async P1
// (docs/reference/frontend-stack.md §4), minus the dependency (which is awkward
// under React 19). On each route it sets <title>, the meta description, the
// canonical link, and the Open-Graph/Twitter title+description+url. The STATIC
// defaults (og:image, og:type, og:site_name, twitter:card, og:locale) live in
// index.html; this hook overrides the per-page ones. Copy lives in locales/de/seo.

import { useEffect } from 'react';

// Canonical/OG URLs always point at production, regardless of the dev/preview
// host they render on (preview builds shouldn't claim their own canonical).
const SITE_ORIGIN = 'https://kurrentschrift.ink';

function upsertMeta(attr: 'name' | 'property', key: string, content: string) {
  const selector = `meta[${attr}="${key}"]`;
  let el = document.head.querySelector<HTMLMetaElement>(selector);
  if (!el) {
    el = document.createElement('meta');
    el.setAttribute(attr, key);
    document.head.appendChild(el);
  }
  el.setAttribute('content', content);
}

function removeMeta(attr: 'name' | 'property', key: string) {
  document.head.querySelector(`meta[${attr}="${key}"]`)?.remove();
}

function upsertCanonical(href: string) {
  let el = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]');
  if (!el) {
    el = document.createElement('link');
    el.setAttribute('rel', 'canonical');
    document.head.appendChild(el);
  }
  el.setAttribute('href', href);
}

export interface PageMeta {
  title: string;
  description: string;
  // The 404 sets this: nginx answers every unknown URL with 200 + the shell, so
  // without it each mistyped link would be an indexable soft-404 that even
  // declares itself canonical. `noindex` swaps the canonical for a robots
  // noindex; every indexable page clears that again (each route runs this hook,
  // so the swap can't stick across a client-side navigation).
  noindex?: boolean;
}

export function usePageMeta({ title, description, noindex = false }: PageMeta) {
  useEffect(() => {
    // nginx and the router serve /quiz/ exactly like /quiz — canonicalize to
    // the slashless form so the SPA never mints trailing-slash duplicates.
    const path = window.location.pathname.replace(/\/+$/, '') || '/';
    const url = SITE_ORIGIN + path;
    document.title = title;
    upsertMeta('name', 'description', description);
    if (noindex) {
      upsertMeta('name', 'robots', 'noindex,follow');
      document.head.querySelector('link[rel="canonical"]')?.remove();
    } else {
      removeMeta('name', 'robots');
      upsertCanonical(url);
    }
    upsertMeta('property', 'og:title', title);
    upsertMeta('property', 'og:description', description);
    upsertMeta('property', 'og:url', url);
    upsertMeta('name', 'twitter:title', title);
    upsertMeta('name', 'twitter:description', description);
  }, [title, description, noindex]);
}
