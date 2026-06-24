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
}

export function usePageMeta({ title, description }: PageMeta) {
  useEffect(() => {
    const url = SITE_ORIGIN + window.location.pathname;
    document.title = title;
    upsertMeta('name', 'description', description);
    upsertCanonical(url);
    upsertMeta('property', 'og:title', title);
    upsertMeta('property', 'og:description', description);
    upsertMeta('property', 'og:url', url);
    upsertMeta('name', 'twitter:title', title);
    upsertMeta('name', 'twitter:description', description);
  }, [title, description]);
}
