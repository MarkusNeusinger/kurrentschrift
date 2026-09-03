// "Only the newest request may write" — the guard every panel needs that reloads
// on a switch and cannot cancel the request it leaves behind.
//
// A `cancelled` flag in an effect cleanup covers the unmount case; it does not
// cover the one that actually bites here: two loads for two different subjects,
// where the OLDER response lands last and sticks. The panel then shows the
// previous subject's numbers under the current subject's name, with no error to
// hint at it, until something reloads. Sequence numbers are the fix, and they
// are pure logic — so they live here with a test rather than inline in a
// component where only a browser could ever check them.

/** Opens a request and returns the predicate "mine is still the newest". */
export type BeginRequest = () => () => boolean;

/**
 * A fresh sequence counter. Call the returned function when a request starts;
 * call ITS result before writing anything the response produced.
 *
 * ```ts
 * const begin = useRef(latestRequestGate()).current;
 * const isCurrent = begin();
 * load().then((data) => isCurrent() && setData(data));
 * ```
 *
 * One gate per panel, held in a ref: a gate recreated on render would count
 * every request as the newest and guard nothing.
 */
export function latestRequestGate(): BeginRequest {
  let newest = 0;
  return () => {
    const mine = ++newest;
    return () => mine === newest;
  };
}
