### Added

- **IndexNow: every deploy tells Bing, Yandex, Seznam, Naver and Yep which
  pages changed.** Bing Webmaster Tools' first recommendation for the site. A
  public key file (`app/public/kurrentschrift-indexnow-….txt`, served by nginx
  like the other machine files) proves control of the host, and the new
  `.github/workflows/indexnow-submit.yml` POSTs the ten sitemap URLs to
  `api.indexnow.org` on every push to `main` that touches `app/**` — the same
  paths that trigger the Cloud Build deploy — or on demand. Ten pages make the
  whole sitemap the natural unit; a diff-to-route mapping would be more code
  than the site has routes. Google does not take part and keeps reading the
  sitemap; the protocol is free (#491).
