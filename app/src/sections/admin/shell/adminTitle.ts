// What the browser tab says while the workbench is open.
//
// The admin used to keep whatever title the last public page had set — a cold
// load showed the site's default, a walk from /quiz left the quiz's standing —
// so two open admin tabs were indistinguishable. This module derives the title
// from the URL alone: the same subject the view's h1 spells out, plus the area
// word, „Buchstabe n · Werkbank".
//
// Deliberately NOT usePageMeta/seo.ts. That hook also writes canonical, og:*
// and twitter:*, which a route behind Cloudflare Access and `Disallow: /admin`
// has no business minting, and the seo catalogue is count-pinned to the public
// routes (routes/seoCoverage.test.ts) — an admin entry there turns it red.
//
// Pure, like focus.ts beside it: pathname + search in, string out, so the whole
// mapping is unit-tested and AdminLayout keeps one effect and no branches.

import { de, fmt } from '@/locales/admin';
import { paths } from '@/routes/paths';

import { readJoinFocus, readLetterFocus, readWordFocus, textForKey } from './focus';

// The area word every admin title ends in — the same one the view headers wear
// as their eyebrow, so tab and page name the place identically.
const AREA = de.admin.shell.startEyebrow;

// The subject line of one view: the detail heading when the URL carries a
// subject, the overview title when it does not. `null` means there is no
// subject at all (the Vorlage picker at /admin), which gets the bare area word.
function subjectOf(pathname: string, search: string): string | null {
  const params = new URLSearchParams(search);
  // A trailing slash is not produced by any of our links, but a hand-typed URL
  // may carry one and must not fall through to the bare area word.
  const path = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;

  if (path === paths.admin.letters) {
    const { glyphKey } = readLetterFocus(params);
    if (!glyphKey) return de.admin.letters.overviewTitle;
    return fmt(de.admin.letters.letterHeading, { key: textForKey(glyphKey) || glyphKey });
  }
  if (path === paths.admin.joins) {
    const { leftKey, rightKey } = readJoinFocus(params);
    if (!leftKey || !rightKey) return de.admin.joins.overviewTitle;
    return fmt(de.admin.joins.joinHeading, { left: leftKey, right: rightKey });
  }
  if (path === paths.admin.words) {
    const { text } = readWordFocus(params);
    if (!text) return de.admin.words.overviewTitle;
    return fmt(de.admin.words.wordHeading, { text });
  }
  if (path === paths.admin.eigenhand) return de.admin.eigenhand.title;
  return null;
}

export function adminTitle(pathname: string, search: string): string {
  const subject = subjectOf(pathname, search);
  return subject ? `${subject} · ${AREA}` : AREA;
}
