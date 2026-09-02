// Strings for the two area hubs (/lesen, /schreiben). Each hub is a small
// overview page that groups its tools as cards, so the top nav stays at three
// entries (Schriftkunde · Lesen · Schreiben). Tone follows the site's quiet,
// turn-of-the-century editorial voice (see /impressum) — warm, not officious.

// `title` is the area's short name (nav, breadcrumbs, the eyebrow over the
// hub's H1); `heading` is the H1 itself and carries the search term (SEO audit
// 2026-08-29, seo.ts); `about` is the one explanatory paragraph a hub owes a
// person — and a search engine — who lands here first: what the script is, for
// whom the tools are, in the words of the Schriftkunde (facts from there).
export const hub = {
  lesen: {
    title: 'Lesen',
    heading: 'Alte deutsche Schrift lesen lernen',
    lead: 'Alte deutsche Handschrift entziffern — Schritt für Schritt. Vom einzelnen Buchstaben bis zum ganzen Wort.',
    // The quiz explains a MISS only for the documented look-alike pairs
    // (sections/quiz/lesefallen.ts: „no explanation is better than an invented
    // one") and never for whole words — so the promise here names the pairs
    // instead of claiming every Fehlgriff (website audit 2026-09-02).
    about:
      'Wer heute einen Brief der Urgroßmutter, ein Kirchenbuch oder eine Feldpostkarte aufschlägt, steht meist vor der deutschen Kurrentschrift — und ihrer späten Schulform, der Sütterlin, die bis 1941 in der Schule gelehrt wurde. Die Buchstaben sind dieselben wie heute, nur ihre Gestalt ist eine andere: Das e sieht aus wie ein n, das u trägt zur Unterscheidung einen Bogen, und das lange ſ wird gern für ein f gehalten. Gelesen lernt man sie so, wie sie damals geschrieben wurde — Buchstabe für Buchstabe und dann im ganzen Wort. Drei Hilfen stehen dafür bereit: das Lese-Quiz, das abfragt und dir bei den klassischen Verwechslern das Merkmal nennt, an dem du die Form das nächste Mal erkennst; die Schreibtafel, die jede Vorlage Buchstabe für Buchstabe zeigt; und die Lesart-Prüfung für das eine Wort, das sich nicht entziffern lassen will. Worin sich Kurrent, Sütterlin und Offenbacher unterscheiden, erklärt die Schriftkunde.',
    cards: {
      quiz: {
        title: 'Lese-Quiz',
        body: 'Erkenne die Buchstaben in einem kurzen Abfragespiel — vom einzelnen Zeichen bis zum ganzen Wort.',
        cta: 'Quiz öffnen',
      },
      tafel: {
        title: 'Schreibtafel',
        body: 'Die drei historischen Vorlagen auf einen Blick — die Sütterlin schreibt sich Zug um Zug selbst. Zum Vergleichen und Nachschlagen.',
        cta: 'Zur Tafel',
      },
      vergleichen: {
        title: 'Lesart prüfen',
        // Careful with the promise: the readings need a dictionary on the
        // server, and until it is loaded the page can only write the guess and
        // show the confusable pairs (website audit 2026-09-02).
        body: 'Ein Wort aus deinem Brief, eine Vermutung — die Feder schreibt sie, daneben die Verwechsler, an denen das Entziffern hängt. Kennt das Wörterbuch ähnliche Wörter, stehen sie dabei.',
        cta: 'Lesart prüfen',
      },
    },
  },
  schreiben: {
    title: 'Schreiben',
    heading: 'Kurrent und Sütterlin selbst schreiben',
    lead: 'Selbst zur Feder greifen. Übe die Züge auf dem ausgedruckten Übungsblatt — oder sieh der Feder beim Schreiben zu.',
    about:
      'Schreiben ist der kürzeste Weg zum Lesen: Wer einmal selbst gespürt hat, wie das lange ſ oben spitz zuläuft und das f seine Schleife bekommt, verwechselt die beiden nicht mehr. Deshalb lohnt der Griff zur Feder auch für alle, die eigentlich nur entziffern wollen. Viel braucht es nicht — ein Blatt mit Lineatur, eine Vorschrift und Geduld. Das Übungsblatt druckt die Lineatur der gewählten Ausgangsschrift als PDF auf DIN A4 — Kurrent (2 : 1 : 2, geneigt), Sütterlin (1 : 1 : 1, aufrecht) oder Offenbacher — mit Schräglinien und Federwinkel nach Wahl, auf Wunsch mit deinem Text als Vorschrift in den Zeilen. Die Federprobe zeigt vorher, wie jeder Zug gesetzt wird und wo ein Buchstabe in den nächsten übergeht. Eine gewöhnliche Füllfeder genügt: Die Sütterlin ist eine Gleichzugschrift und verlangt keinen Druckwechsel.',
    cards: {
      worksheet: {
        title: 'Übungsblatt',
        body: 'Erzeuge ein Übungsblatt mit Lineatur als PDF — Verhältnis, Schräglinien und Federwinkel frei wählbar, auf Wunsch mit deinem Text als Vorschrift, fertig zum Ausdrucken.',
        cta: 'Blatt erzeugen',
      },
      federprobe: {
        title: 'Federprobe',
        body: 'Tippe einen beliebigen Text — die Feder schreibt ihn dir lebendig in Sütterlin, mit allen Übergängen.',
        cta: 'Feder ansetzen',
      },
    },
  },
} as const;
