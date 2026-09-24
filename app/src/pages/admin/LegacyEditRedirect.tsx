import { Navigate, useParams } from 'react-router-dom';

import { lettersUrl } from '@/sections/admin/shell/focus';

// `/admin/edit/:glyphKey` — the chart editor's retired address from the days
// when every letter had a page of its own. The editor lives inside the
// Buchstaben view now, whose subject rides in the query (`?g=`), so the
// redirect carries the letter across instead of dropping it on the overview:
// a bookmark to `a` should open `a`. No key check here — the view's own reader
// (`focus.ts::readLetterFocus`) already sends a key the registry does not know
// to the overview, which is where the old redirect sent every key.
//
// A page of its own and lazy like the others, because the route table is in
// the entry chunk and `focus.ts` is admin code the public pages never need.
export default function LegacyEditRedirect() {
  const { glyphKey } = useParams();
  return <Navigate to={lettersUrl(glyphKey)} replace />;
}
