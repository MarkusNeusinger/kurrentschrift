### Changed

- **Kein Zustand der Werkbank lebt mehr nur im Hover.** Jeder `Tooltip` und
  jedes `title=` unter `/admin` ist durchgegangen und nach einer mechanischen
  Frage sortiert worden — ist das Kind des Tooltips überhaupt fokussierbar?
  Was einen Zustand, einen Grund, eine Zahl oder eine Anweisung trug und an
  einem nicht klickbaren Chip, einer `Typography` oder dem `<span>` um eine
  deaktivierte Schaltfläche hing, ist jetzt sichtbarer Text oder steht hinter
  einem `InfoHint` — einem echten Knopf mit Fokusring und 44-px-Fläche, der auf
  Klick öffnet und darum auch unter dem Finger funktioniert. Betroffen sind
  unter anderem: warum „Einrichten" und „Diagnose" grau sind (steht als Zeile
  im Chart-Kopf), warum eine Sortierung nicht wählbar ist, die sechs
  Sensorwerte hinter einem Streifen-Befund, die Rohzahlen eines Paares, die
  Notiz einer angeschnittenen Wortprobe und der Wortlaut eines Ladefehlers.
  Neu in `design-system.md` als **§9.4 (bindend)**, mit der Regel „höchstens
  EIN `InfoHint` je Zeile".

- **Die Abzüge einer Buchstaben-Zeile haben eine ehrliche Erklärung statt sechs
  winziger.** Jede Kategorie war eine 22 px hohe `Typography` mit eigenem
  `tabIndex` — ein Tab-Stopp ohne Fokusring, auf einer Listenseite bis zu 72
  Stück, und keiner davon mit dem Finger erreichbar. Die Zahlen bleiben alle
  sichtbar; erklärt werden sie von `ScoreHelp`, dem einen `InfoHint` der Zeile,
  der auch sagt, was der Score ist, warum eine Form keinen trägt und was
  „Fit ⌀" misst. Gemessen am Wegwerf-Stack: 151 → 94 Tab-Stopps auf
  `/admin/buchstaben`, 5 → 3 je Zeile.

- **Der Auftragskorb-⚑ der Kopfleiste trägt kein Zahlen-Badge mehr.** MUI setzt
  dessen Ziffer in 12 px, unter dem Typo-Boden, und sagte in Farbe, was die
  Scope-Leiste eine Zeile tiefer in Worten sagt („⚑ 3 offen" im Vorlagen-Feld).
  Das Icon behält seinen benannten `aria-label` und bekommt die 44-px-Fläche.

### Added

- **Der Fokusring ist ein geteiltes Token.** `focusRing` wohnt in
  `app/src/styles/focusRing.ts`, neben `hitArea`, und das Theme importiert es
  für seine drei MUI-Regeln. Vorher war es eine modul-private Konstante — womit
  jedes selbstgebaute fokussierbare Element ohne Ring blieb, allen voran die
  Deckungs-Zellen der Eigenhand: nackte `<button>` mit `appearance: none`, die
  bei Fokus gar nichts zeigten. Ein Unit-Test prüft die IDENTITÄT des Objekts in
  den Theme-Regeln, nicht seine Gleichheit — ein zweites Literal mit denselben
  Zahlen ist genau die Drift, gegen die der Export geschrieben ist.

### Fixed

- **Die Lupe der Eigenhand-Galerie war per Tastatur nicht erreichbar.** Der
  Öffner war ein `<img onClick>` ohne Rolle, ohne `tabIndex` und ohne
  Tastenbehandlung; er entkam der ESLint-Regel nur, weil das JSX-Element `Box`
  heißt. Jetzt ein `ButtonBase` mit eigenem Namen („S0001 · F01 groß ansehen"),
  der auf Enter öffnet. Dasselbe für die Zeile des Auftragskorbs, die ein
  `<p role="link">` mit handgebautem Enter/Leertaste-Handler war.

- **Trefferflächen unter dem 44-px-Boden in der Werkbank.** „Buchstabe wählen"
  (32,5 px), der ‹ ›-Schritt und der Buchstaben-Chip des Kopfes, die vier
  `?reiter=`-Schalter der Eigenhand (40,5 px), die Deckungs-Zellen (33 px), die
  Knöpfe des Korb-Schubfachs, die Werkzeugleiste des Charts und die
  Paar-Auswahl der Übergänge wachsen auf den Boden — gewachsen, nicht
  überlagert, weil sie dicht beieinanderstehen. Gemessen mit
  `npm run touch-targets --routes /admin/…`: 97 → 0 Verstöße über die vier
  Admin-Routen; `npm run type-floor` dort ebenfalls von 4 auf 0.

- **`touch-targets` maß das falsche Element an einem Eingabefeld.** MUI rendert
  ein Select als Combobox-`div` plus ein unsichtbares `<input>`, das nur für das
  Absenden eines Formulars existiert; das Skript maß dieses 21 px hohe Hemd
  statt des 44 px hohen Feldrahmens. Ein Eingabefeld wird jetzt am FELD
  gemessen — derselbe Gedanke, mit dem ein in ein `<label>` gewickeltes
  Bedienelement schon am Label gemessen wurde. Ein Feldrahmen unter dem Boden
  fällt weiterhin durch.
