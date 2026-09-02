### Fixed

- **The Lesart vocabulary can be loaded at all.** The batch endpoint read
  before it wrote — a `SELECT … WHERE gen = ? AND (key, word) IN (<batch>)`
  over the generation as it grew — so the load got slower the more of it was
  done: 0.42 s for the first 5 000 words, 16.2 s once 80 000 were in, which
  extrapolates to minutes per batch and hours in total against Cloudflare's
  100 s origin cut. It is now one `INSERT … ON CONFLICT DO NOTHING` per chunk,
  dialect-aware and paged under asyncpg's 32 767 bind parameters, and the
  reported `inserted` count is what the statement actually added. The whole
  718 665-word vocabulary now loads in 144 flat batches — 0.21 s the first,
  0.27 s the last, 0.18–0.41 s across the run, 34 s in total.
- **A 67-character compound no longer kills the run.** Two words the igerman98
  expansion produces are longer than the `lesart_forms.word` column, and the
  API refuses the entire batch that carries one — batch 17 of the first
  production attempt died on it. The bound now lives once, as
  `core.lesarten.WORD_MAX`, the loader drops what exceeds it and says how
  many, and the server keeps its 400 as the defence for every other client.
- **The loader prints the seconds each batch took.** The number that grew is
  the one the first two attempts had no way to see.
