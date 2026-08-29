"""The Lesart vocabulary's local half: expand the igerman98 dictionary
(`expand`) and push the words, unioned with the quiz bank, into the shared
database through the admin API (`sync`). Tools never write the DB themselves
(docs/reference/werkzeuge.md); the bucket keys are computed server-side by
core.lesarten so the load and the read can never disagree."""
