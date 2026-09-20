### Changed

- **The Eigenhand strip surface is a set of files, not one 1318-line panel.**
  `StripsPanel.tsx` had grown to hold the blob loader, the path loader, the
  viewport observer, the Bahn overlay and its caption, the raw-reading chips,
  the Befund chips, the strip tile, the gallery tile, the gallery with its
  pager and the Lupe — all beside its own listing, filter and switches. Each is
  now its own module next to it, and the panel keeps what it alone owns: the
  listing, the search, the shared zoom, the three switches and the Fleckenmaske
  write-back. Nothing about the surface changes — the rendered strip list and
  the filtered gallery are identical before and after, down to the markup, and
  no suite moved. It is preparation: the Tintentreue traffic light, the
  per-Kasten Nachfahr-Liste, the editor entry point and the box PATCH all land
  on this surface, and four changes fighting over one file is how a panel that
  size gets worse rather than better.
