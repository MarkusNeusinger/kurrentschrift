export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const targetPath = url.pathname.replace(/^\/api/, '');
    const targetUrl = `https://api.kurrentschrift.ink${targetPath}${url.search}`;
    const headers = new Headers(request.headers);
    headers.delete('host');
    // The API's origin gate (api/origin_gate.py) admits only requests that
    // carry the secret Cloudflare stamps at the edge. A Worker subrequest to
    // the same zone skips the zone's Transform Rules, so the Worker stamps the
    // header itself from its secret binding (unset binding = nothing stamped).
    if (env.ORIGIN_SECRET) headers.set('X-Origin-Secret', env.ORIGIN_SECRET);
    return fetch(targetUrl, {
      method: request.method,
      headers,
      body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : null,
      redirect: 'manual',
    });
  },
};
