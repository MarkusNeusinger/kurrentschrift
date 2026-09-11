# Die Welle: Bahn-Rückgewinnung, kohärente Verformung und Schlangen — was die Literatur und das eigene Journal zur Physik-Bedingung sagen

> **Status (2026-09-11): Befund-Journal.** Momentaufnahme der vier
> Recherche-Berichte vom Nachmittag des 2026-09-11, die der Welle-Runde
> vorausgingen (§14 „Welle `sep11`" in
> [`../reference/messjournal.md`](../reference/messjournal.md)); fortgeschrieben
> wird sie nicht, die gebauten Arme und ihre Zahlen wohnen im Journal und
> auf [`../reference/verfahren-tintenpfad.md`](../reference/verfahren-tintenpfad.md).
> Anlass war die Bedingung des Autors vom Mittag: „Die Punkte können sich
> nur so, wie so eine Welle, zusammenhängend verschieben." Die vier
> Berichte haben drei Dinge geliefert, die die Runde entschieden haben.
> **(1) Eine Konstruktionsregel:** Kohärenz muss ein PARAMETERRAUM oder ein
> CONSTRAINT sein, nie ein Gewicht und nie eine Nachbearbeitung — das
> Journal hatte die Straftermvariante (`--letter-smooth`,
> Displacement-Steifigkeit bei 0,0), die Nachglättung (Lotse v0.6) und die
> Blende (R3, +1 626 Knicke) bereits gemessen verworfen, während die harte
> B-Spline-Basis (LF11, 96,7 % Lückenschluss bei neutralem Lineal) als
> einzige alle Gates bestand (§4). **(2) Eine Maßzahl:** die Breite jeder
> Welle wird in STÜTZPUNKTEN deklariert, nicht in Federbreiten — Proben
> liegen 0,0282–0,0286 xh auseinander, die gemessene Rippel hat 0,29 xh ≈
> 7 Anker Periode, also muss jeder Mechanismus mindestens ~6 Stützpunkte
> breit koppeln; die Eigenspektren sagen, was das kostet (240 DOF je
> Buchstabe heute gegen 31–38 bei β = 0,30 xh, §2–§3). **(3) Eine
> Reihenfolge:** Tinte zuerst, Zuordnung danach (Nel/du Preez/Herbst,
> Qiao & Yasuhara, Kato & Yasuhara) statt Saat hinlegen und punktweise
> verbiegen (§1). Gebaut wurden daraus drei Arme (§5): der Tintenpfad
> (bestätigt), die Wellen-Basis (Physik geliefert, Tor an den
> Tinten-Umkehren gerissen) und die Schlange (Zickzack praktisch weg,
> Lineal verloren). Mitgenommen und noch nicht gebaut: der monotone
> DP-Korrespondenz-Arm mit harter Nachbarschranke, der
> Varifold-/korrespondenzfreie Tintenterm, die Unschärfe-Leiter im Folger
> und Σ-Λ zuerst als SENSOR. Die Warnung über allem: das eingefrorene
> Lineal ist gegenüber dem Zittern nicht nur blind, es belohnt es
> stellenweise — Ansprüche laufen über die referenzfreien Sensoren, das
> Lineal wird als Preis mitberichtet. Nichts hier ändert eine
> Entscheidung; die `research/`-Schicht folgt dem Code nie.

## 1 Bahn-Rückgewinnung aus Tintenbildern (offline → online)

Vor der Literatur stand eine Messung am eigenen Stand. Auf dem
Referenzkandidaten `temp/coarse-sep10/affine/a1/cand.json` (13
Schleifen-Wörter, xh 30–32 px) beträgt der mediane Ausgabe-Schritt
**0,0286 xh = 0,82–0,94 px**, ein Wort trägt **611–2305 Punkte** (Median
1042), und mit 120 Ankern je Buchstabe plus 22 Verbinder-Ankern hängen an
einem Wort rund **2·10³ freie Parameter**, deren einzige Kopplung
untereinander die Tikhonov-Leine zur Saat ist. Die Deformationsbasis hat
also 1-px-Auflösung: der punktweise Wackler ist exakt darstellbar und wird
nur bepreist (`lsmooth_op`, `bind_op`), nie unmöglich gemacht. Genau das
unterscheidet uns von der Literatur — dort ist er in **beiden** Familien
nicht darstellbar.

**Familie A — Tinte zuerst, Buchstaben danach.** Skelett, Graph aus
Endpunkten/Verzweigungen und Kanten, dann eine Traversierung wählen: Jäger
löst das als globale Optimierung (TSP) unter der Annahme kleinster
Krümmung; Kato & Yasuhara typisieren erst global alle Kanten und verfolgen
dann ab einem Startknoten, mit expliziter Behandlung doppelt gezogener
Linien; Qiao & Yasuhara definieren die glatteste Bahn als **optimalen
Euler-Pfad**, bewerten Fortsetzungen über „direction context" und erkennen
Doppelstriche per maximalem gewichtetem Matching (Auswertung auf ~13 000
Unipen-abgeleiteten Bildern); Nguyen & Blumenstein bringen den
Mehrstrich-Fall und die „ambiguous zone" an Knotenklumpen — genau unsere
Kreuzungen bei 30 px x-Höhe. Der Pfad ist eine Kette ganzer Skelettkanten;
ein einzelner Punkt KANN nicht zacken. Die skelettfreie Variante derselben
Idee sucht im gehobenen Zustandsraum (x, y, θ) — Tintenpixel × 16
Richtungs-Bins ≈ 3·10⁴ Zustände — den kürzesten Weg mit Richtungswechsel
als Kosten (Dijkstra/A*); sie ist dort robust, wo Skelette brechen (Blobs,
verschmolzener Toner — die Flecken, für die die 1,5-mm-Bürste gebaut
wurde), und ihre Schwachstelle ist die Abdeckung: ein kürzester Weg lässt
die Gegenseite einer Schleife gern aus, weshalb `paper_len_xh` und
Abdeckung IMMER zusammen zu lesen sind.

**Familie A', unser Fall wörtlich.** Nel, du Preez & Herbst bauen ein HMM
AUS dem statischen Bild (Zustände = Tintenpositionen, Übergänge = zulässige
Stiftbewegungen) und dekodieren eine BEKANNTE dynamische Referenz hindurch.
Wir kennen das Wort, und `core/compose.py` liefert die dynamische Referenz
mit dem richtigen Duktus. Größenordnung nach Bericht: 1,5–3·10³
ausgedünnte Tintenpixel je Wort, mit 16 Tangenten-Bins 3–5·10⁴ Zustände,
Beam 200–500 — weit innerhalb des Budgets von einer bis zehn Minuten je
Wort. Die Buchstabenzuordnung fällt als Stufenindex gratis ab; Doppelzüge
(Sütterlin-t-Stamm, ſ) müssen explizit als Zustand modelliert werden, sonst
weigert sich der Dekoder zu retracen. Die Zuordnung danach ist in der
Literatur eine **monotone** Korrespondenz (Uchida & Sakoe): Monotonie und
Stetigkeit sind Constraints der DP-Gitterübergänge, kein Strafterm — eine
Probe kann nicht rückwärts oder seitwärts auf den Nachbarstamm springen.

**Die Spurenkunde.** Doermann & Rosenfeld ordnen die zeitlichen Indizien in
der ruhenden Tinte: Linienenden, Tintenstau an Richtungswechseln,
Verjüngung beim Absetzen, glatte Fortsetzung an Kreuzungen,
Über-/Unterlagerung an Schnittpunkten. Das ist unsere Zwei-Kanal-Doktrin
(Breite = Druck, Schwärzung = Tintenmenge) als Evidenzmodell — und der
Folger liest heute nur das Geometriefeld. Daraus fällt ein referenzfreier
Sensor, der keine Glätte-Näherung ist: der Anteil der Richtungsumkehren
eines Kandidaten, der auf einem Stau-Ort liegt. Eine Umkehr am Stau ist
motiviert, eine mitten im glatten Bogen ist ein Wackler.

**Die gelernte Familie** (für uns kein Folger, aber ein Prior, den wir
gratis trainieren könnten, weil unser Komponist beliebig viele
Bild/Bahn-Paare rendert): Encoder-Decoder (Bhunia), TRACE mit DTW als
Trainingsverlust (scheitert systematisch an i-Punkten, t-Strichen und
Strichenden — denselben Stellen wie wir), sub-stroke-Transformer, und
zuletzt bildkonditionierte Diffusion, die die GANZE Bahn gemeinsam
entrauscht und explizit gegen fragile Skelett-Zwischenstufen und gegen
autoregressive Fehlerakkumulation argumentiert. Bemerkenswert für die
Vergleichbarkeit: die ACCV-2022-Arbeit definiert **AIoU** und **LDTW** —
das Maßpaar, das unser dev-19-Lineal ohnehin fährt.

**Quellen §1:**
Jäger, Recovering Dynamic Information from Static Handwritten Word Images (ICPR 1996, Langfassung) [PDF](https://www.researchgate.net/profile/Stefan-Jaeger-4/publication/2819972_Recovering_Dynamic_Information_from_Static_Handwritten_Word_Images/links/5ad8c3c3458515c60f5a5c86/Recovering-Dynamic-Information-from-Static-Handwritten-Word-Images.pdf) — Kleinste-Krümmung-Annahme, Rekonstruktion als TSP über den Skelettgraphen ·
Jäger, Recovering Writing Traces in Off-line Handwriting Recognition (ICPR 1996) [IEEE](https://ieeexplore.ieee.org/document/1363897/) ·
Kato & Yasuhara, Recovery of Drawing Order from Single-Stroke Handwriting Images (PAMI 22(9), 2000) [Semantic Scholar](https://www.semanticscholar.org/paper/Recovery-of-Drawing-Order-from-Single-Stroke-Images-Kato-Yasuhara/e6505c74c1db2084642d82877c4f4fc2e9a5c22b) — globale Kantentypisierung, dann Verfolgung; explizite Doppelstriche ·
Qiao & Yasuhara, Recovering Drawing Order … Direction Context and Optimal Euler Path (ICASSP 2006) [IEEE](https://ieeexplore.ieee.org/document/1660455/) ·
Qiao & Yasuhara, Recovering Dynamic Information from Static Handwritten Images (IWFHR 2004) [PDF](https://www.cse.lehigh.edu/prr/Biometrics/Archive/Papers/QY04.pdf) ·
Qiao & Yasuhara, Recognition-directed recovering of temporal information (PRL 2006) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167865505001674) — die REC–REC-Schleife ·
Nguyen & Blumenstein, Recovery of drawing order from multi-stroke English handwritten images (ESWA 2016) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0957417416304109) ·
Nguyen & Blumenstein, Techniques for static handwriting trajectory recovery: a survey (DAS 2010) [ACM](https://dl.acm.org/doi/pdf/10.1145/1815330.1815390) · [PDF-Kopie](https://www.researchgate.net/profile/Vu-Nguyen-22/publication/220933198_Techniques_for_static_handwriting_trajectory_recovery_A_survey/links/55c5805208aeb9756741f6d4/Techniques-for-static-handwriting-trajectory-recovery-A-survey.pdf) ·
Diaz, Crispo, Parziale, Marcelli & Ferrer, Writing Order Recovery in Complex and Long Static Handwriting (IJIMAI 2022) [arXiv](https://arxiv.org/abs/2406.03194) · [PDF](https://arxiv.org/pdf/2406.03194) ·
Nel, du Preez & Herbst, Estimating the Pen Trajectories of Static Signatures Using HMMs (PAMI 27(11), 2005) [PubMed](https://pubmed.ncbi.nlm.nih.gov/16285373/) — das nächste publizierte Analogon zu „bekanntes Wort + komponierte Saat" ·
Nel, du Preez & Herbst, Estimating the Pen Trajectories of Multi-Path Static Scripts Using HMMs [ResearchGate](https://www.researchgate.net/publication/232655063_Estimating_the_Pen_Trajectories_of_Multi-Path_Static_Scripts_Using_Hidden_Markov_Models) ·
Uchida & Sakoe, A Survey of Elastic Matching Techniques for Handwritten Character Recognition (IEICE 2005) [PDF](http://human.ait.kyushu-u.ac.jp/~uchida/Papers/e88-d_8_1781.pdf) · Buch-Preprint [PDF](https://human.ait.kyushu-u.ac.jp/publications/EM-book-preprint.pdf) ·
Doermann & Rosenfeld, Recovery of temporal information from static images of handwriting (IJCV 15, 1995) [Springer](https://link.springer.com/article/10.1007/BF01450853) ·
Plamondon & Privitera, The segmentation of cursive handwriting (IEEE TIP 1999) [Semantic Scholar](https://www.semanticscholar.org/paper/The-segmentation-of-cursive-handwriting:-an-based-Plamondon-Privitera/8c80e777b92b6587d7097efaaeb2f0e04182bace) ·
Bhunia et al., Handwriting Trajectory Recovery using End-to-End Deep Encoder-Decoder Network (ICPR 2018) [arXiv](https://arxiv.org/abs/1801.07211) ·
Archibald et al., TRACE (ICDAR 2021) [arXiv](https://arxiv.org/abs/2105.11559) ·
Nagamatsu, Toyota & Uchida, Handwriting Trajectory Recovery with Diffusion Models (2026) [arXiv](https://arxiv.org/html/2607.03422v1) ·
Complex Handwriting Trajectory Recovery: Evaluation Metrics and Algorithm (ACCV 2022) [PDF](https://arxiv.org/pdf/2210.15879) — definiert AIoU und LDTW ·
Handwriting Trajectory Recovery via Autoregressive Ordered Stroke Instance Prediction (2026) [arXiv](https://arxiv.org/html/2609.02251) ·
ICDAR 2013 Competition on Handwriting Stroke Recovery from Offline Data [ResearchGate](https://www.researchgate.net/publication/261349666_ICDAR_2013_Competition_on_Handwriting_Stroke_Recovery_from_Offline_Data)

## 2 Kohärente Verformung: die Welle als Parameterraum, nicht als Preis

Der Satz des Autors — „die Punkte können sich nur wie eine Welle
zusammenhängend verschieben" — hat in der Registrierungs-Literatur einen
Namen: **Motion Coherence**. Myronenko & Songs Coherent Point Drift
regularisiert nicht die Form, sondern das VERSCHIEBUNGSFELD; die
Variationslösung ist v = G·w mit G einem Gauß-Kern, das Feld ist also
bandbegrenzt. Yuille & Grzywacz' Theorie steht dahinter, Lüthi et al.
verallgemeinern sie zum Gaußprozess-Prior, dessen führende
Karhunen-Loève-Moden (Nyström) eine kleine explizite Basis bilden; Dölz et
al. liefern die Fehlerschranke für „wie viele Moden".

Gemessen wurde das an unseren echten Ankern (Artefakte und Skripte in
`temp/wellen-sep11/registrierung/`, `messung_basis.py`, BLAS gepinnt). Der
It.-17-Solve trägt **820–3084 freie Parameter je Wort** (406–1530 freie
Anker, 615–2325 EDT-Proben), also **240 Freiheitsgrade je Buchstabe** bei
120 Ankern. Das Eigenspektrum eines Gauß-Kerns über die ECHTEN Anker
(Arc-Length-Kern, 99 % Kernenergie) sagt, wie wenig davon eine Welle
braucht: bei β = 0,30 xh **31–38 DOF je Buchstabe**, bei β = 0,60 xh
**16–19**, bei β = 1,00 xh **10–12**. Auf Wortebene fällt `die` von 722 auf
92 und `Galoppieren` von 2642 auf 354 (je β = 0,3 xh). Der Kern muss dabei
entlang der BOGENLÄNGE laufen, nicht in der Ebene: der Ebenen-Kern ist
zwar 25–40 % sparsamer in Moden, verklebt aber die beiden Äste einer
Kreuzung (`f`, die k-Unterschleife), die der Stift zeitlich weit
auseinander geschrieben hat — physikalisch falsch und genau die
Buchstaben, die noch scheitern. Rechenzeit ist kein Argument: die
Eigenzerlegung kostet 0,02 s (406 Anker) bzw. 0,67 s (1530 Anker) mit
einem BLAS-Thread, während ein ganzer Wort-Solve heute 3,5–165 s braucht —
gegen das Budget des Autors von 60–600 s.

Die Alternativen zum Kern sind dieselbe Mechanik mit anderer Basis.
**B-Spline-Freiform** (Rueckert; Schnabel mehrstufig/nicht-uniform): ein
kubischer Kontrollpunkt bewegt vier Knotenspannen, kürzer als eine
Knotenspanne ist nichts darstellbar. Gemessen: eine Buchstabenbahn ist
5,5–7,0 xh lang, bei h = 0,5 xh sind das 14–17 Kontrollpunkte = 28–34 DOF
(vergleichbar mit β = 0,6), bei h = 0,25 xh 50–62 DOF; ein 2-D-Gitter
über den ganzen Wort-Ausschnitt (16 × 2 xh, h = 0,5) hätte ~33 × 5 = 165
Kontrollpunkte = 330 DOF für ein Wort, achtmal weniger als die 2642 von
`Galoppieren` heute. Rueckerts diffeomorphe Variante liefert dazu eine
harte, prüfbare Bedingung: Kontrollpunkt-Verschiebung unter 0,4 ×
Gitterabstand ⇒ faltungsfrei. **Thin-Plate-Splines** (Bookstein; Chui &
Rangarajan mit Softassign und Ausreißer-Bin) sind der natürliche Ersatz
der Affin-Saat: bei L = 6–12 Landmarken kostet eine TPS 2(L+3) = 18–30
DOF je Buchstabe und ist eine geschlossene Form, also Millisekunden —
bezahlt macht sich das, weil `die` und `das` heute 2700–3200
L-BFGS-Iterationen aus der Affin-Saat verbrennen und `Galoppieren` in die
Deckelung bei 8100 läuft. Donato & Belongie sowie Yangs Revisit sagen, wie
man verhindert, dass EINE falsche Korrespondenz den ganzen Buchstaben
biegt.

Drei weitere Mechanismen, die keine Basis sind: (a) **Metrik statt
Modell** — Demons glättet entweder das Update-Feld (viskos, erlaubt große
kumulierte Deformation) oder das Gesamtfeld (elastisch, hält das Endfeld
bandbegrenzt); die Energie bleibt unberührt, nur der Weg dorthin ist eine
Welle (die Sobolev-Variante steht in §3). (b) **Harte Nachbarschranke per
DP** — Amini, Weymouth & Jain lösen Snake-Energien als mehrstufigen
Entscheidungsprozess; dort sind harte Ungleichungen zwischen Nachbarn
natürlich formulierbar, in einem Variationslöser gar nicht. |δᵢ − δᵢ₋₁| ≤
ε heißt: ein zackender Anker hat keinen zulässigen Übergang. Bei ~0,9 px
Ankerabstand bedeutet ε = 0,1 xh, dass sich das Feld je x-Höhe Stiftweg
um höchstens ~3 px biegen darf; eine Leiter von 21–41 Normalen-Stufen
über 1530 Anker sind ~2,6 Mio. Übergangsauswertungen, also Sekunden. Und
DP ist global optimal — das einzige Verfahren der Liste, das auch die
verbliebenen Nicht-Konvexitäten (k-Schleife, a→n-Naht, ſt→r) angeht. (c)
**Diffeomorphe Obergrenze** — LDDMM mit Varifold-Datenterm (Glaunès;
Charon & Trouvé) vergleicht KURVEN als geometrische Maße, braucht also gar
keine Punkt-Zuordnung; genau das umgeht den gemessenen Treiber, dass die
Deckungs-Kraft an einem gestrandeten Anker **32-fach** ist und mit Kosinus
**−0,996** entgegengesetzt zeigt. Größenordnung: T = 10 Zeitschritte ×
Kontrollpunkte alle 0,5 xh ≈ 2600 Parameter je Wort — wie heute, aber
jeder davon kohärent.

Die stehende Warnung des Berichts gilt für jede dieser Bauten: **Kohärenz
erbt die Fehler des Datenterms.** Wo heute ein Anker ins Papier gezogen
wird, zieht ein kohärentes Feld deren zwanzig mit; `--paper-weight 30` und
ein symmetrischer Präzisions-/Recall-Tintenterm (wie in
`tools/pairlab/affinereg.py`) müssen scharf bleiben.

**Quellen §2:**
Myronenko & Song, Point Set Registration: Coherent Point Drift (PAMI 32(12), 2010) [arXiv](https://arxiv.org/abs/0905.2635) · [PDF](https://arxiv.org/pdf/0905.2635) ·
Myronenko, Song & Carreira-Perpiñán, Non-rigid point set registration (NIPS 2006) [PDF](https://proceedings.neurips.cc/paper/2006/file/3b2d8f129ae2f408f2153cd9ce663043-Paper.pdf) · [Kurzfassung](https://graphics.stanford.edu/courses/cs468-07-winter/Papers/nips2006_0613.pdf) ·
Lüthi, Jud, Gerig & Vetter, Gaussian Process Morphable Models (PAMI 2018) [arXiv](https://arxiv.org/abs/1603.07254) ·
Dölz et al., Error-Controlled Model Approximation for Gaussian Process Morphable Models (JMIV 61, 2019) [Springer](https://link.springer.com/article/10.1007/s10851-018-0854-5) ·
pycpd — CPD in reinem NumPy mit `low_rank`/`num_eig` [GitHub](https://github.com/siavashk/pycpd) (lesen, nicht importieren: Werkzeuge fügen dem Solve-Pfad keine Abhängigkeit hinzu) ·
Yuille & Grzywacz, A mathematical analysis of the motion coherence theory (IJCV 3(2), 1989) — keine URL im Bericht ·
Rueckert et al., Nonrigid Registration Using Free-Form Deformations (IEEE TMI 18(8), 1999) [IEEE](https://ieeexplore.ieee.org/document/796284/) · [Lesefassung](https://www.sfu.ca/~kabhishe/posts/posts/summary_tmi_freeformdeformations_1999/) ·
Schnabel et al., Non-uniform Multi-level Free-Form Deformations (MICCAI 2001) [Springer](https://link.springer.com/chapter/10.1007/3-540-45468-3_69) ·
Rueckert et al., Diffeomorphic Registration Using B-Splines (MICCAI 2006) [PubMed](https://pubmed.ncbi.nlm.nih.gov/17354834/) ·
Tustison, Avants & Gee, Explicit B-spline regularization in diffeomorphic image registration [PMC](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC3870320/) ·
Bookstein, Principal Warps (PAMI 11(6), 1989) [Semantic Scholar](https://www.semanticscholar.org/paper/Principal-Warps:-Thin-Plate-Splines-and-the-of-Bookstein/427e2415d0d8f846cdabba34842162f7bab6af02) ·
Chui & Rangarajan, A new point matching algorithm for non-rigid registration (CVIU 89, 2003) [PDF](https://www.cise.ufl.edu/~anand/pdf/rangarajan_cviu_si_final.pdf) ·
Donato & Belongie, Approximation Methods for Thin Plate Spline Mappings and Principal Warps [PDF](https://cseweb.ucsd.edu/~sjb/pami_tps.pdf) ·
Yang, The TPS-RPM algorithm: a revisit (PRL 32(7), 2011) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167865511000304) ·
Uchida & Sakoe, Eigen-deformations for elastic matching (Pattern Recognition 2003) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0031320303000396) ·
Vercauteren, Pennec, Perchant & Ayache, Diffeomorphic Demons (NeuroImage 45(1), 2009) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1053811908011683) · ITK-Fassung 2007 [PDF](https://www.sci.utah.edu/~wolters/LiteraturZurVorlesung/Literatur/F:_Anisotropy/Vercauteren_DiffeomorphicDemons-Paper_2007.pdf) · SimpleITK-Referenz [Doxygen](https://simpleitk.org/doxygen/v2_5/html/classitk_1_1simple_1_1DiffeomorphicDemonsRegistrationFilter.html) ·
Amini, Weymouth & Jain, Using Dynamic Programming for Solving Variational Problems in Vision (PAMI 12(9), 1990) [IEEE](https://ieeexplore.ieee.org/document/57681/) · [PDF](https://www.researchgate.net/profile/A-Amini/publication/3191827_Using_Dynamic_Programming_for_Solving_Variational_Problems_in_Vision/links/00b7d531bedc4775a8000000/Using-Dynamic-Programming-for-Solving-Variational-Problems-in-Vision.pdf) ·
Glaunès, Qiu, Miller & Younes, Large Deformation Diffeomorphic Metric Curve Mapping (IJCV 80(3), 2008) [PDF](https://helios2.mi.parisdescartes.fr/~glaunes/preprints/GlaunesQiuCurve08.pdf) ·
Charon & Trouvé, The varifold representation of non-oriented shapes (SIAM J. Imaging Sci. 6(4), 2013) [PDF](https://arxiv.org/pdf/1304.6108) ·
Younes, Diffeomorphic Mapping and Shape Analysis [Ressourcenseite](https://www.cis.jhu.edu/~younes/LDDMM.html) ·
Ge, Fan & Ding, Non-rigid Point Set Registration with Global-Local Topology Preservation (CVPRW 2014) [PDF](https://openaccess.thecvf.com/content_cvpr_workshops_2014/W04/papers/Ge_Non-rigid_Point_Set_2014_CVPR_paper.pdf) ·
Ge & Fan, Non-rigid Articulated Point Set Registration with Local Structure Preservation (CVPRW 2015) [PDF](https://openaccess.thecvf.com/content_cvpr_workshops_2015/W05/papers/Ge_Non-Rigid_Articulated_Point_2015_CVPR_paper.pdf)

## 3 Schlangen und elastische Kurven: Metrik, Basis und die Physik der Hand

Die Snake-Linie beantwortet dieselbe Frage von der Kurvenseite — und sie
ist in unserem Fall zuerst gemessen worden (Skript und Protokoll:
`temp/wellen-sep11/snakes/measure_band.py`, `band-measurement.txt`, BLAS
gepinnt). Über die zwölf Schleifen-Wörter liegen **14 391 gespeicherte
Proben**, mediane x-Höhe 31,0 px, Probenabstand **0,0284 xh (0,88 px)**,
Anker ~1,3 px auseinander (1,5 Proben je Anker). Vor allem aber: **das
Zittern ist eine RIPPEL, kein einzeln zuckender Punkt.** Der Seitenversatz
gegen einen kubischen B-Spline mit 0,25-xh-Knoten wechselt alle **5,5
Proben (4,8 px)** das Vorzeichen bei **0,0116 xh (0,36 px)** RMS — Periode
≈ 10 Proben ≈ **0,29 xh ≈ 7 Anker**. Das ist die Kohärenzlänge, die jeder
Wellen-Mechanismus überschreiten MUSS. Die Nachtschleife hat diese Rippel
nicht angefasst (Basis 0,0117 xh / 5,0 Proben gegen It. 17 0,0116 / 5,5);
was `--kink-weight` bewegt hat, ist das Krümmungsspektrum: der Anteil der
Wendeleistung unterhalb 0,25 xh fiel 0,606 → 0,502, unterhalb 0,1 xh
0,138 → 0,083. Der Strafterm bepreist also die schärfsten Zacken und lässt
die Rippel stehen.

Die **Bandbreiten-Tabelle** sagt, wo eine Basis liegen darf
(LSQ-Kubik-Spline gegen die eigene Geometrie des Folgers, Median über
Züge): h = 1,0 xh → 3,71 px RMS; 0,5 → 1,35; 0,35 → 0,85; **0,25 → 0,50**;
0,15 → 0,25; 0,10 → 0,15 px. Weil der Geometrieterm ein Feld liest, das
bei `DIST_FIELD_SIGMA_PX` = 1,0 px geglättet ist, wirft eine Basis bei
h = 0,25 xh nichts weg, was der Datenterm überhaupt sehen kann (1687
Kontrollpunkte über zwölf Wörter gegen 14 391 Proben, Maximalfehler 2,09
px) — und die 0,29-xh-Rippel liegt außerhalb. Brigger, Hoeg & Unser
liefern dazu das Argument, dass die krümmungsbeschränkt optimale Snake
ohnehin ein kubischer Spline ist: setzt man die Eigenskala (den
Knotenabstand) a priori, wird der innere Energieterm — und mit ihm das
Gewichte-Tuning — überflüssig.

**Metrik statt Modell.** Kass, Witkin & Terzopoulos steigen nie den rohen
L2-Gradienten ab: der semi-implizite Schritt (A + γI)⁻¹ ist die Inverse
einer bandierten Steifigkeitsmatrix, also eine Glättung — jeder Schritt
IST eine Welle. Sundaramoorthi, Yezzi & Mennucci verallgemeinern das zum
H1-/Sobolev-Gradienten und zeigen im Fourier-Bild, dass der Fluss
nachweislich grob-nach-fein läuft; Charpiat et al. liefern das Argument,
das diese Familie von der verworfenen Straftermfamilie trennt: das
Skalarprodukt ist ein Prior auf den ABSTIEG, nicht auf die Energie —
dieselben kritischen Punkte, anderer Weg. Für unsere Rippel (Periode ~7
Anker) folgt direkt λ ≈ 7⁴ ≈ 2,4·10³ am groben Ende der Leiter. Dazu
gehört die Feldseite: Blake & Zisserman (GNC) und Mobahi & Fisher
begründen die Unschärfe-Leiter, Xu & Prince (GVF) und Cohen (Ballon) die
Reichweite — bei uns eher klein, weil das Ziel bereits ein dünnes Skelett
mit geglättetem EDT ist; die messbare Hälfte ist die LEITER. Heute läuft
die Saat über σ = 4, 2, 1 px (`affinereg.py`), der Folger dann in einer
einzigen feinen Skala — genau der Übergang, an dem eine 0,29-xh-Rippel
entstehen kann. Laufzeit-Rahmen: `follow.json` meldet 198,8 s für 13
Wörter bei `--jobs 4`, also ~61 s CPU je Wort; das Budget des Autors
erlaubt das Ein- bis Zehnfache.

**Generativ und elastisch.** Revow, Williams & Hinton haben unsere
Architektur schon 1996 als Ziffernmodell gebaut: deformierbarer B-Spline
mit Gauß-„Tintengeneratoren" plus Gleichverteilungs-Rauschkomponente, per
EM angepasst, mit Feder zur Heimatform — das ist unsere Saat plus
`e_geo`, nur mit den Freiheitsgraden an Kontrollpunkten statt bei 0,88
px. Hinton & Nair ersetzen den Spline später durch einen Feder-Stift,
dessen Steifigkeitsfolge das Motorprogramm ist. Zhu & Yuilles Region
Competition formuliert den Besitzanspruch auf Daten als Teil der
Zielfunktion — der Rahmen für unsere Frage, welchem Segment ein
Skelettpunkt gehört. Die elastische Metrik (SRVF: Srivastava et al., Mio
et al., Younes, Lahiri et al.) trennt STRECKEN von BIEGEN mit eigenen
Gewichten: eine Laufform-Weitung von 3–11 % ist dann eine kostenlose
Umparametrisierung, die Rippel dagegen teuer — die richtige Währung für
„die Komposition darf gebogen werden, sie ist nur die Saat". Caselles'
Geodesic Active Contours nennt der Bericht ausdrücklich als den Weg, den
wir NICHT gehen: er wirft Parametrisierung und Strichreihenfolge weg, also
den Duktus-Prior selbst.

**Das strenge Ende: die kinematische Theorie.** Plamondons Σ-Λ-Modell
beschreibt eine Bahn als Überlagerung lognormaler
Geschwindigkeitsimpulse, iDeLog extrahiert die Parameter aus einer
statischen Spur in einer dualen räumlich-kinematischen Schleife; ein
Buchstabe kostet dann ~6 Parameter je Lognormal-Zug (≈ 24–48 DOF), und
der Wackler hat keinen Parameter, in dem er leben könnte. Flash & Hogans
Minimum-Jerk und Todorov & Jordans Glattheits-Maximierung sind dieselbe
Aussage von der optimalen-Steuerung-Seite. Der ehrliche Einwand des
Berichts: die Theorie setzt SCHNELLE Bewegung voraus, eine 1922er
Lehrhand schreibt langsam und mit gewollten Spitzen und Doppelzügen, und
die Zeitachse ist in einer gedruckten Platte gar nicht enthalten.
Empfehlung deshalb: zuerst als **Sensor** (Σ-Λ an die zwölf
Referenzspuren fitten und berichten, wie viele Lognormale ein
Sütterlin-Buchstabe braucht), erst danach als Parametrisierung.

**Quellen §3:**
Kass, Witkin & Terzopoulos, Snakes: Active Contour Models (IJCV 1988) [Springer](https://link.springer.com/article/10.1007/BF00133570) · [PDF (LPI)](https://www.lpi.tel.uva.es/muitic/pim/docus/Snakes.pdf) · [PDF (UCLA)](https://web.cs.ucla.edu/~dt/papers/ijcv88/ijcv88.pdf) ·
Brigger, Hoeg & Unser, B-Spline Snakes (IEEE TIP 9(9), 2000) [PDF](https://bigwww.epfl.ch/publications/brigger9901.pdf) ·
Sundaramoorthi, Yezzi & Mennucci, Sobolev Active Contours (IJCV 73(3), 2007) [Springer](https://link.springer.com/article/10.1007/s11263-006-0635-2) · Coarse-to-Fine Segmentation and Tracking Using Sobolev Active Contours (PAMI 2008) [PDF](https://cvgmt.sns.it/media/doc/paper/1050/pami07_revised.pdf) · New Possibilities with Sobolev Active Contours (IJCV 84, 2009) [Springer](https://link.springer.com/article/10.1007/s11263-008-0133-9) ·
Charpiat, Maurel, Keriven, Pons & Faugeras, Generalized Gradients: Priors on Minimization Flows (IJCV 73(3), 2007) [PDF](https://www.lri.fr/~gcharpia/gradients.pdf) ·
Blake & Zisserman, The Graduated Non-Convexity Algorithm [MIT Press](https://direct.mit.edu/books/monograph/3877/chapter/162976/The-Graduated-Non-Convexity-Algorithm) ·
Mobahi & Fisher, Coarse-to-Fine Minimization of Some Common Nonconvexities [PDF](https://people.csail.mit.edu/hmobahi/pubs/common_nonconvex_2015.pdf) ·
Xu & Prince, Snakes, Shapes, and Gradient Vector Flow (IEEE TIP 7(3), 1998) [PubMed](https://pubmed.ncbi.nlm.nih.gov/18276256/) · Generalized Gradient Vector Flow External Forces (Signal Processing 71(2), 1998) [PDF](https://iacl.ece.jhu.edu/pubs/p105j.pdf) ·
Cohen, On Active Contour Models and Balloons (CVGIP:IU 53(2), 1991) [PDF](https://www.lpi.tel.uva.es/muitic/pim/docus/cohen.pdf) ·
Revow, Williams & Hinton, Using Generative Models for Handwritten Digit Recognition (PAMI 18(6), 1996) [PDF](https://homepages.inf.ed.ac.uk/ckiw/postscript/pami.pdf) · [Kopie](https://www.cs.toronto.edu/~hinton/absps/pamirevow.pdf) ·
Hinton & Nair, Inferring Motor Programs from Images of Handwritten Digits (NIPS 2005) [PDF](https://www.cs.toronto.edu/~hinton/absps/vnips.pdf) ·
Zhu & Yuille, Region Competition (PAMI 18(9), 1996) [PDF](https://www.cnbc.cmu.edu/~tai/papers/region_competition.pdf) ·
Younes, Computable Elastic Distances Between Shapes (SIAM J. Appl. Math. 58(2), 1998) [PDF](https://jasoncantarella.com/downloads/younes.pdf) ·
Srivastava, Klassen, Joshi & Jermyn, Shape Analysis of Elastic Curves in Euclidean Spaces (PAMI 33(7), 2011) [PDF](https://www.math.fsu.edu/~whuang2/pdf/Elastic_Shape_Analysis_techrep.pdf) · [Zweitfassung](https://citeseerx.ist.psu.edu/document?doi=a94f78f54a7b597d124d9bfaeec44dad5e858bef&repid=rep1&type=pdf) ·
Mio, Srivastava & Joshi, On Shape of Plane Elastic Curves (IJCV 73(3), 2007) [Springer](https://link.springer.com/article/10.1007/s11263-006-9968-0) ·
Lahiri, Robinson & Klassen, Precise Matching of PL Curves in the Square Root Velocity Framework [PDF](https://arxiv.org/pdf/1507.02728) ·
Sorkine & Alexa, As-Rigid-As-Possible Surface Modeling (SGP 2007) — keine URL im Bericht ·
Caselles, Kimmel & Sapiro, Geodesic Active Contours (IJCV 22(1), 1997) [ACM](https://dl.acm.org/doi/10.1023/A%3A1007979827043) — ausdrücklich der NICHT eingeschlagene Weg ·
Ferrer, Diaz, Carmona-Duarte & Plamondon, iDeLog (PAMI 2020) [PubMed](https://pubmed.ncbi.nlm.nih.gov/30403620/) ·
Plamondon, A kinematic theory of rapid human movements (Biological Cybernetics I–IV) [ResearchGate](https://www.researchgate.net/publication/271086989_A_kinematic_theory_of_rapid_human_movements) ·
O'Reilly & Plamondon, Development of a Sigma-Lognormal representation for on-line signatures (PR 42(12), 2009) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0031320308004470) ·
Djioua & Plamondon, Studying the variability of handwriting patterns using the Kinematic Theory (HMS 28(5), 2009) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0167945709000190) ·
Plamondon et al., Extraction of delta-lognormal parameters from handwriting strokes (FCS 2007) [Springer](https://link.springer.com/article/10.1007/s11704-007-0009-0) ·
Ferrer et al., Synthetic on-line signature generation, Part I (Pattern Recognition 45(7), 2012) [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0031320311005127) ·
Plamondon & Privitera, The segmentation of cursive handwriting (IEEE TIP 8(1), 1999) [PubMed](https://pubmed.ncbi.nlm.nih.gov/18262867/) ·
Flash & Hogan, The coordination of arm movements (J. Neurosci. 1985) — Minimum Jerk, keine URL in dieser Sitzung verifiziert ·
Todorov & Jordan, Smoothness maximization along a predefined path (J. Neurophysiol. 1998) [Physiology](https://journals.physiology.org/doi/full/10.1152/jn.1998.80.2.696)

## 4 Was das Journal schon verworfen hatte — und was bestanden hat

Der vierte Bericht hat nicht die Literatur, sondern das eigene Messjournal
gelesen, und er kommt mit einer scharfen Aussage zurück: **dieses Repo hat
die Frage des Autors dreimal gemessen, auf drei Ebenen, und die Ergebnisse
zeigen in dieselbe Richtung.**

**Die Krankheit ist benannt und beziffert.** `core/aggregate.py::_median_and_mad`
mediant jeden der 120 Anker UNABHÄNGIG — „benachbarte Anker werden
unabhängig gemediant" —, und die gespeicherten Laufform-Zeilen zittern
deshalb mit **6,86 Krümmungsumkehren je x-Höhe** gegen **0,23** der Tafel
(Laufform LF11 `sep02`). Der Folger hat eine Ebene höher exakt dieselbe
Architektur: Deltas je Anker, ohne Kopplung außer der Tikhonov-Leine.

**Die einzige Kur, die je alle Gates bestanden hat, ist eine harte,
parameterarme BASIS, kein Strafterm.** LF11 projiziert jedes Vorkommen auf
einen geklemmten kubischen B-Spline über die Tafel-Bogenlänge (Ecken als
Knoten der Vielfachheit 3, eine Basis je Zug) und mediant die
KONTROLLPUNKTE: bei Δs 0,16 xh schließt das **96,7 %** der Zickzack-Lücke
(6,864 → 0,449 je xh), das Wort-Lineal bleibt neutral (0,109255 →
0,109218, Paare 0,148433 → 0,148198), **kein** Wort verliert eine
Kreuzung, und LF10s unabhängige Formdistanz-Spalte FIEL sogar (Median-Δ
des p90 −0,012 Federradien über 22 Zeilen). Die Leiter klammert das ein:
0,08 xh schließt nur 73 %, 0,32 xh fängt an, Form zu bewegen (+0,00323
Bench, 15 Wörter gewinnen Kreuzungen). Der Code ist da und rein:
`core/aggregate.py::_knot_vector` + `BSpline.design_matrix`.

**Strafterm und Nachbearbeitung sind beide gemessen negativ.**
`--letter-smooth` (der Zweite-Differenzen-Preis auf der Verschiebung, der
Schalter „Formglätte" der Nachtschleife) ist negativ; die
Displacement-Steifigkeit im Kettenlöser steht bei 0,0, weil sie zwar
gestrandete Anker 98 → 41 und das Spitzenverhältnis 2,90 → 1,59
verbesserte, aber den Anteil der Anker NEBEN der Tinte um 18 % hob und
`not_converged_local` 21 → 31 — „aus einem Anker im Papier werden drei".
Lotse v0.6 (Laplace-Glättung der fertigen Bahn) brach alle drei Gates (dtw
0,0578 → 0,0860, aiou −0,022, Struktur-Zähler nicht byte-gleich). Und R3s
C¹-Blende scheiterte an einer LÄNGE, die seither Konstruktionsregel ist:
Stützpunkte liegen 0,0265 xh auseinander (nachgemessen 0,0282 xh, p10
0,0252 / p90 0,0326 über 15 097 Segmente auf
`temp/coarse-sep10/affine/a1/cand.json`), die deklarierte Blende
überspannte 2,74 davon — „die Blende blendet nicht", +1 626 neue
Knick-Ereignisse. **Eine kohärente Verformung muss ~6 Stützpunkte breit
sein oder breiter** (Δs 0,16 xh ≈ 5,7 Punkte). Dieselbe Aussage IM SOLVE
(R3c, quadratische Hinge auf ein Distanzfeld, über `sampling_op` gefaltet)
kostete dagegen nichts: Knick-Ereignisse 2 296 → 2 258, Median 8,08° →
7,53° — „die Glätte ist umsonst zu haben".

**Die kreuzungssichere Form eines Verschiebungsfeldes ist ebenfalls
gemessen.** Lotse v0.10 hängte Punkt-Knoten ans Feld und verlor Kreuzungen
genau dort, wo sie dicht liegen — Diagnose wörtlich: „das Offset-Feld der
Punkt-Knoten variiert nahe der Kreuzung zu schnell — Scherung und
Mittelung zerstören genau die Transversalität". v0.11 machte dieselben
Offsets zu lokal KONSTANTEN Plateaus (0,35 xh, überlappende Plateaus
global per Union-Find verschmolzen) und wurde adoptiert: `cross_missing`
3 → 1, Kreuzungs-Positionsfehler 0,116 → 0,066 xh (−43 %). Eine reine
lokale Translation erhält jedes X exakt; Scherung gehört in die
kreuzungsfreien Strecken. v0.12 (Plateau-Sehne) zeigt die Gegenfalle: „der
Wackel WAR das X", `cross_missing` 1 → 8.

**Die niederfrequente Hälfte der Welle ist die Saat.** Der eingefrorene
Sensor `tools.pairlab.seedgap` trennt Saat-Versatz (Platzierung) von
Saat-Rest (Form); über die 44 beurteilten Wörter sagt der Saat-Rest
sichtbare Papier-Umkehren mit Pearson **+0,691** (partiell +0,592) voraus
gegen +0,417/+0,157 für die Platzierung, Terzile 0,020 · 0,059 · 0,239
Papier-Umkehren je Slot. Der Arm `--chain-seed grid` heilt das Wort des
Beurteilers (`unter` +0,1072 aiou, 5 → 0 Papier-Umkehren) und bricht zwei
Gates — ein ehrliches Negativ mit zwei benannten Konversionen. In
`regieren` wollen die acht Slots −0,600 … +0,367 xh, eine Spanne von
0,967 xh: ein globaler Versatz kann das nicht ausdrücken.

**Tinte zuerst ist gebaut und vermessen.** Der Lotse fährt den
Skelettgraphen mit dem Duktus nur als Karte an Entscheidungspunkten
(dev-19 dtw-Median 0,053386 · p90 0,116668 · aiou 0,7473 · `cross_missing`
**0** — die einzige Route ohne fehlende Kreuzung, Stand `sep07`, Wurzel
`ccb036a5eb20…`). Die prior-freie Kontrolle routeg zeigt, was Tinte allein
kauft und kostet: aiou **0,8333** (beste Deckung aller Routen) bei dtw
0,8198 = 13-fach der Kette, 15 von 23 Kreuzungen und ALLE Retraces
verloren, 90 zusätzliche Absetzer. InkSight roh liegt bei 0,0956 ≈ 1,5-fach
der Kette, ist an Kreuzungen sauber, 2,9-fach besser auf `muß`, verliert
aber 11–12 von 15 Retrace-Zonen.

**Die Abnahme-Instrumente sind älter als diese Runde.** `core/continuity.py`
liest `kink = |2·turn(W₁) − turn(2·W₁)|` bei W₁ = 0,0725 xh (halbe Feder),
Schwelle θ = arcsin(0,2) = 11,537° — exakt null für einen Kreisbogen JEDES
Radius, ungleich null nur, wo sich Wendung in einen Punkt drängt;
Duktus-Ereignisse sind ausgenommen und werden gezählt. Es hat bereits R3
(+1 626), R3b (+462), R3c (−38) und R4 (+34) benotet. Wichtig ist die
Lektion von LF11: **das eingefrorene Lineal ist gegenüber dem Zittern
nicht nur blind, es belohnt es stellenweise** — eine zappelnde Mittellinie
streift mehr Specimen-Tinte (`Sporn` +0,0440 am Lineal, sichtbar besser).
Ebenso zeigt die Registrierungs-Messung, dass eine reine Glattheits-Zahl
je Probe nichts entscheidet: Basis 512 Knicke / Σ|d2| 121,3 xh gegen It.
17 341 / 75,2 — aber die eingefrorenen MENSCHLICHEN Referenzzeilen liegen
selbst bei 443 / 133,8.

**Und die Entscheidbarkeit begrenzt jede Wellen-Runde.** K-F erzeugte
einen unfreiwilligen Nulltest: für 23 von 63 Wörtern unterschied sich das
Init-Ankerfeld um höchstens 1,78·10⁻¹⁵ (die nächste Klasse beginnt bei
0,00346) — und auf dieser bedeutungslosen Störung kippten **neun**
Wächter-Verdikte, aiou schwankte −0,0298 … +0,0800. Seither gilt: kein
Init-/Saat-Arm ist WORTWEISE entscheidbar. Dazu die Wächter-Körnung (auf
dem R3c-Arm verloren 26 von 63 Wörtern ihre Runde ganz oder teilweise; 13
Wörter fallen auch unter v5 auf den Init zurück, darunter `kann` und
`haben`) und die Augen-Runden selbst: Runde 7 gab 63,5 % „kein
Unterschied" bei einer medianen Bewegung von 0,0221 xh, Runde 9 sogar 44
von 44. Wer das Bild um weniger als ~0,1 xh bewegt, bekommt vom Auge kein
Urteil.

**Quellen §4** (alle im Repo; die §14-Anker im
[Register](../reference/messjournal.md#register-der-einträge-index-keine-zahl-heimat)
des Journals): Laufform LF11 `sep02` (Vorregistrierung und Messung: der
Mechanismus in fünf Schritten, die Δs-Leiter, 96,7 % Lückenschluss, die
Blindheit UND die Belohnung des Lineals) · `core/aggregate.py::spline_basis_median`
/ `_knot_vector` (geklemmter Knotenvektor mit Eck-Vielfachheit) · Route
„Lotse" v0.10 / v0.11 / v0.12 `aug19` (Punkt-Knoten verworfen, Plateau-
Anker adoptiert, die Plateau-Sehne als Falle) · Lotse Absprung-Forensik
`sep04` · Kette K-G `sep09` (Diagnose + gemessen: Saat-Versatz gegen
Saat-Rest, die Slot-Spanne 0,967 xh in `regieren`) · Kette K-E `sep09`
(Runde 9: 44 von 44) · Route „Lotse" `aug16` und
[`../reference/verfahren-lotse.md`](../reference/verfahren-lotse.md) ·
Route G `aug14` und Route B T0 `aug15`,
[`../reference/verfahren-nullprobe.md`](../reference/verfahren-nullprobe.md)
· Kette R3 / R3c / R4 `sep07` (die Stützpunkt-Messung 0,0265 xh, das
Blenden-Versagen, die Hinge im Solve, der Tinte-zuerst-Attraktor) · Kette
K-C `aug20` und K-D `aug21` (Evidenz-Hygiene, Ausflug-Inventur) ·
Übergänge S2 `sep06` (der Unstetigkeits-Sensor) und `core/continuity.py`
(`KINK_WINDOW_UNITS` 0,0725, Schwelle `degrees(asin(0,2))`) · Route
„Lotse" v0.6 `aug16` (Nachglättung verworfen) ·
`tools/pairlab/follow.py::FollowWeights.letter_smooth` und
`tools/pairlab/affinereg.py` · Kette K-F `sep04` (der 1,78·10⁻¹⁵-Nulltest)
· [`../reference/verfahren-kette.md`](../reference/verfahren-kette.md) ·
[`../proposals/tintenfolger.md`](../proposals/tintenfolger.md) §7.3, §7.9,
§7.11 · Arm ① `aug14` und Arm ⑨ `aug16` (die Leine hält allein die
Struktur; „eine andere Formulierung" als einziger Weg).

## 5 Was wir daraus gebaut haben — Tintenpfad, Wellen-Basis, Schlange

Aus der Karte wurden am 11.9. drei Bauten, jeder von einem unabhängigen
Prüfer nachgemessen (Berichte: `temp/wellen-sep11/pruefer-tintenpfad/`,
`…/pruefer-wellen-basis/`, `…/pruefer-schlange/`; alle Läufe BLAS gepinnt,
Wurzel `ccb036a5eb20…`). Bezugsgrößen: der Kandidat der Nachtschleife It.
17/18 (`temp/coarse-sep10/`) und die Produktionsbasis
`temp/coarse-sep10/tb/base-dev.json`. It. 18 stand auf 63 Wörtern bei
Papier 13 · Strecke 23,5 xh · dtw 0,044128 · p90 0,086332 · aiou 0,7821 ·
12:7 (Basis 49 · 61,7 · 0,045881 · 0,088356 · 0,7660). Die gebuchten
Zahlen und Verdikte stehen in §14 „Welle `sep11`" und „Tintenpfad-Arme
`sep11`"; hier steht, was jeder Bau aus §1–§4 umgesetzt hat.

**(a) Tintenpfad — Tinte zuerst, Buchstaben danach (bestätigt; PR #591,
gemergt `de178b1`).** Die Umsetzung von §1: Stufe 1 baut STRÄNGE aus dem
eingefrorenen Tintenskelett ohne Prior (Spur-Beschnitt unter 0,15 xh,
glatteste Fortsetzung an jedem Knoten, jedes Pixel per Zelt-Fit auf der
Distanztransformation auf die Mittelachse gesetzt); Stufe 2 nimmt aus der
komponierten Saat nur die REIHENFOLGE und dekodiert sie per Viterbi durch
die Stränge (Zustände = Strangpixel × Richtung + PAPIER, monotone Fahrten,
bepreiste Haarnadeln, Sprünge unter 0,35 xh). Die Verformung ist damit gar
keine Verschiebung von Stützpunkten mehr: die Bahn IST die Tintenachse,
frei sind nur diskrete Entscheidungen, von denen jede einen ganzen Strang
bewegt. Sensoren: 13 Zeilen **0 · 93 · 0,78 xh** (It. 17: 18 · 162 ·
29,87), 63 Wörter **0 · 331 · 1,49** (Basis 49 · 742 · 61,73). Lineal dev-19
gegen die Basis: dtw-Median **0,044230**, p90 0,090673, aiou 0,7867,
gepaart 7 besser : 12 schlechter (Vorzeichentest p = 0,35928),
`cross_spurious` 9 → 3, `cross_missing` 11 → 14, Retrace-Lücke 0,252 →
0,134. Der Prüfer hat die Physik unabhängig gelesen: Abstand der
gelieferten Bahn zum eingefrorenen `ref_skel` Median **0,42 px** / p90
0,66 / p99 1,11, nur 0,3 % der Bahn mehr als 2 px neben der Tinte — gegen
It. 17 0,79/2,17/3,88 (12,1 %), Basis 0,84/2,24/6,77 (12,4 %) und die
MENSCHLICHE Referenzspur 0,82/1,87/3,14 (8,0 %); Anteil der Proben
innerhalb der Maske 1,000 gegen 0,943/0,904. Bei fester
0,10-xh-Richtungsfensterung: Wendewinkel-p90 41,8° gegen 59,5/60,8 (Hand
30,8), Gesamtwendung 189 °/xh gegen 229/231 (Hand 144). Ehrliche
Soll-Seite, vom Prüfer benannt: zwei der drei Sensoren sind für eine
skelettgebundene Bahn **konstruktionsbedingt vakuum** (Papier 0,
Papier-Strecke ≈ 0); der Arm nutzt 13 Absetzer gegen 8 (It. 17) und 4 der
Hand; der Roh-Knick liegt bei 9,74° gegen 6,76° (It. 17) und 7,87° (Hand);
und gegen den AKTUELL BESTEN Arm statt gegen die Basis ist das Lineal ein
Unentschieden (It. 17: 0,044431 / 0,08397 / 0,7894). Die zwölf Verlierer
sind die kurzen Nicht-Schleifen-Wörter bei +0,001…+0,009, die sichtbare
Restschuld sitzt an den ENDEN.

**Die fünf Arme darauf (PR #592, gemergt `1879f3d`, Messungen in
`temp/tintenpfad-sep11/<arm>/MESSUNG.md`)**: Spitzen (Bahn bis ans
Maskenende lesen), Stummel (Verzweigungs-Stummel absorbieren), Normalen-Fit
(feinere EDT-Lesung), Tinten-Brücke (Sehne nur über blasse Tinte),
Doppelstrich (Retrace, wo die Tinte doppelt ist). Drei tragen, die
Kombination steht als Kandidat: 13 Zeilen **0 · 95 · 1,34** (davon Maske
0,76), Knick **8,3°**; 63 Wörter **0 · 330 · 4,77** (Maske 1,32), dtw
**0,041356**, p90 0,091040, aiou 0,7876, **18:1 gegen #591**, 9:10 gegen
die Basis, 10:9 gegen It. 18 (aus den Reports nachgezählt; der PR-Text
hat die beiden letzten vertauscht). Zwei Arme sind ehrliche Negative mit
Rettungsweg: der Stummel-Filter bleibt inert, und die Doppelstrich-EVIDENZ
feuert auf der Platte nie — Rettungsweg dort ist die reine Dekoder-Regel
(`ratio 1,0`), also Evidenz weglassen statt Schwelle weichspülen.

**(b) Wellen-Basis — die Kohärenz-Basis im Kettenlöser (teils; Zweig
`wellen-basis-hook-a`, ungemergt).** Genau §2 als Variablenwechsel:
`deltas = B·c` mit B der geklemmten kubischen B-Spline-Designmatrix über
die Saat-Bogenlänge, ein Block je STIFTZUG (durchgehend über
Buchstabennähte, geschnitten nur an zuginternen `stroke_starts`, Knoten
alle Δs = 0,25 xh); nur `unpack`/`_pack` ändern sich, der Gradient ist die
exakte Kettenregel Bᵀg, ein Ein-Anker-Zacken ist nicht im Parameterraum.
Die Physik ist geliefert und vom Prüfer mit eigenen Sensoren bestätigt:
Aus-und-zurück-Zacken (zwei Wendungen ≥ 45° mit entgegengesetztem
Vorzeichen über Sehnen ≤ 0,12 xh) **49 → 11 (−78 %)**, zweite Differenz je
Sehne 0,1834 → 0,1313 (−28 %), Spitzen-Zensus über 15 057 Vertices / 427
xh: Vertices über 0,005 xh 1 826 → 993 (4,25 → 2,32 je xh), scharfe Ecken
≥ 90° 262 → 255 (die echten Sütterlin-Spitzen bleiben). Lineal dev-19 gegen
die Basis: dtw-Median **0,041403**, p90 0,089618, aiou 0,7978, **15:4
besser** (p = 0,01921) — gegen den Amtsinhaber It. 17 aber 10:9 bei
schlechterem Mittel, p90 und schlechtestem Wert. Und das Gate der Runde
fällt: Tinten-Umkehren **162 → 200 (+23 %)** auf den Zwölfen (63 Wörter
592 → 745), und zwar auf jeder Sprosse der deklarierten Leiter (0,16 /
0,25 / 0,35). Dazu ein Pflicht-Anker-Rückschritt: `das` wird um +0,0782
dtw schlechter, weil das kohärente Feld eine falsch platzierte Affin-Saat
nicht punktweise reparieren kann — es legt eine gerade Sehne durchs Papier
statt in die a-Schale. Genau das ist der benannte Rettungsweg: **die Basis
auf eine Tintenpfad-Saat setzen** statt auf die affine.

**(c) Schlange — die elastische Kurve neben der Kette (teils; Zweig
`wellen-schlange`, ungemergt).** §3 als eigenständiges Werkzeug
`tools/pairlab/schlange.py`: jeder Stift-unten-Lauf zu EINER Kurve
verschweißt, bei h = 0,8 px neu abgetastet (Duktus-Ecken als
Bruchknoten), entwickelt mit dem semi-impliziten Schritt `x += τ·(I +
ℓ⁴·D2ᵀD2)⁻¹·(F_img + F_cov + F_home + F_bend)` über eine σ-2→1-Leiter —
Sobolev-Metrik, Bogenlängen-Parametrisierung und Biegeenergie mit freier
Eckzeile. Sensoren: zwölf Wörter **0 · 78 · 4,47 xh**, 63 Wörter 0 · 272 ·
13,51. Der Prüfer maß mit eigenem, abtast-fairem Sensor (alle Kandidaten
auf 0,032 xh): Zickzack-Ereignisse je xh **Basis 3,718 · It. 17 1,863 ·
Schlange 0,009**, und die Ablation zeigt, dass es der Mechanismus ist und
kein Knopf (ℓ 1 + β_e 0 → 3,08, also der Defekt vollständig zurück; ℓ 7 +
β_e 0 → 0,34; β_e 4 → 0,256; β_e 64 → 0,009). Das Lineal verliert
trotzdem: dtw-Median **0,051445** gegen Basis 0,045881, p90 0,124488, aiou
0,765428, 6:13 — bei gleichzeitig `cross_spurious` 9 → **0** und
Retrace-Lücke 0,252 → 0,162. Der Handel ist dekomponierbar und benannt:
die Bahn wandert nicht mehr ins Papier (Überstand 10,35 % → 1,54 % ihrer
Länge), lässt dafür etwas mehr Tinte unbesucht (9,67 % → 11,11 %); 18 von
111 Kurven im 63er-Lauf sind gestrandete Zeichen (16 u-Bögen, 2 ü), kein
Körperzug. Zwei Prüfer-Funde gehören zur Ehrlichkeit des Eintrags: die
Auswahl β_e = 64 verbiegt die eigene Vorregistrierung (sie strandet den
u-Bogen in `unter`; nach der Regel wie geschrieben gewänne β_e = 16 mit
105 / 5,34 xh), und die Kohärenz-RATIO im Bau-Bericht ist durch die
3–4-fach größere Verschiebungs-Amplitude konfundiert — die Aussage trägt
der Bahn-Sensor, nicht die Ratio. Laufzeit 19,5 s je Wort (Median über
die Zwölf), also weit im Budget.

**Bilanz der Runde.** Der Tinte-zuerst-Zweig ist der einzige, der ein Gate
der Runde ohne Bruch nimmt und inzwischen als Kombination auch das Lineal
gegen die Basis hält; die beiden Physik-Bauten liefern die Kohärenz
messbar und bezahlen sie an je einer anderen Stelle (Tinten-Umkehren bzw.
dtw). Keiner der drei ist als Verfahren adoptiert — der Autor hat Runde 11
ausdrücklich nicht beurteilt („erst grob richtig").

**Artefakte §5** (gitignored, Arbeitsstand außerhalb des Repos):
`temp/wellen-sep11/pruefer-tintenpfad/MESSUNGEN.txt` (Verdikt
„confirmed") · `temp/wellen-sep11/tintenpfad-strang-*/README.md` (Kandidat,
Report-JSONs, JUMP-1.0-Leiter) · `temp/wellen-sep11/pruefer-wellen-basis/path_coherence.py`
(Zacken- und Spitzen-Zensus) · `temp/wellen-sep11/pruefer-schlange/jitter_probe.py`
(abtast-fairer Zickzack-Sensor, Ablation) ·
`temp/wellen-sep11/registrierung/messung_basis.py` (Eigenspektrum, DOF) ·
`temp/wellen-sep11/snakes/measure_band.py` (Probenabstand, Rippel,
Bandbreiten-Tabelle) · `temp/coarse-sep10/affine/a1/cand.json` (der
gemeinsame Messgegenstand) · `temp/tintenpfad-sep11/` (je Arm eine
`MESSUNG.md`, `kombination/`). PRs: #590 (Grob-richtig-Schleife, `ebf5d91`)
· #591 (Tintenpfad, `de178b1`) · #592 (Tintenpfad-Arme, `1879f3d`).
