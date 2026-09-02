// Custom Plausible events.
//
// The counting itself is set up in `index.html`: the queueing stub
// `window.plausible` is defined unconditionally, the SCRIPT that drains the
// queue is added only on the production hostname. So a call from dev or a
// preview build costs one array push and reaches no server — no host check is
// needed here, and none should be added (it would have to be kept in step with
// index.html).
//
// Everything is wrapped: an analytics call must never be the reason a page
// fails to render — which matters most for the one event we send today, the
// 404, whose page is also the fallback of the router's error boundary.

declare global {
  interface Window {
    plausible?: (event: string, options?: { props?: Record<string, string> }) => void;
  }
}

export function trackEvent(event: string, props?: Record<string, string>): void {
  try {
    window.plausible?.(event, props ? { props } : undefined);
  } catch {
    // Deliberately silent.
  }
}
