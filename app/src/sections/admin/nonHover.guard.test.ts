// The non-hover rule, kept from rotting back (V25, design-system.md §9.4).
//
// The rule is mechanical — a `Tooltip` is a NAME for something focusable, and a
// native `title=` reaches neither the keyboard nor the finger at all — but it is
// invisible in a diff: `title={t.someHint}` on a `<Chip>` looks exactly like
// `title={t.panelTitle}` on a `<Panel>`, and the first one hides a definition
// while the second one names a section. The non-hover round classified 48
// tooltips by eye and still missed the seven landmark chips, which is why the
// check is pinned here rather than reviewed again next time.
//
// Two shapes fail:
//   * a native `title=` on a DOM element or a MUI primitive — HTML's own
//     tooltip, hover only, on every browser;
//   * a `tabIndex={0}` WITHOUT a role — the symptom the score breakdown wore:
//     a tab stop that shows nothing and does nothing, added only so a hover
//     could be reached by keyboard. With a `role` it is the opposite case: an
//     SVG marker that really is a control and cannot be a `ButtonBase`
//     (`LandmarkOverlay`, the Wort-Rückgrat) is built by hand, correctly.
//
// `title` on a COMPONENT of ours is a prop, not the HTML attribute — so the
// check names the tags that DO render the attribute (lower-case DOM elements
// and the MUI primitives) instead of trying to list every component we own,
// which would go stale the day someone adds one.

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const ROOTS = ['src/sections/admin', 'src/layouts/admin'];

/**
 * MUI components for which `title` is a prop of their own rather than the HTML
 * attribute. Everything ELSE imported from `@mui/material` spreads unknown
 * props onto its DOM root, so a `title` on it is the native attribute — which
 * is why the check reads each file's own `@mui/material` import list instead of
 * carrying a list of primitives that would go stale the day someone reaches for
 * `Alert` or `FormControlLabel`.
 */
const MUI_TITLE_IS_A_PROP = new Set(['Tooltip']);

/** The component names a file imports from `@mui/material`. */
function muiImports(source: string): Set<string> {
  const names = new Set<string>();
  // Both shapes occur: the multi-line `{ … } from '@mui/material'` block and a
  // default import from a deep path (`@mui/material/Button`).
  for (const match of source.matchAll(/import\s+\{([^}]*)\}\s+from\s+'@mui\/material'/g)) {
    for (const raw of match[1].split(',')) {
      const name = raw.trim().split(/\s+as\s+/).pop()?.trim();
      if (name) names.add(name);
    }
  }
  for (const match of source.matchAll(/import\s+(\w+)\s+from\s+'@mui\/material\/(\w+)'/g)) names.add(match[1]);
  return names;
}

/**
 * Call sites where a native `title` is the untruncated form of a label the
 * element already SHOWS — not hidden state — and therefore legal. Each one is
 * named with its file, so the entry dies with the call site.
 */
const NATIVE_TITLE_ALLOWED = new Set(['shell/OccurrenceThumb.tsx']);

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return walk(path);
    return path.endsWith('.tsx') && !path.endsWith('.test.tsx') ? [path] : [];
  });
}

/**
 * Every JSX opening tag as `[tagName, attributeText]`.
 *
 * Reading forward from `<Tag` and balancing `{}` is enough here and much less
 * than a parser: an attribute value is either a string or a braced expression,
 * and a `>` inside a braced expression (an arrow function, a comparison) is
 * what the depth counter is for.
 */
function openingTags(source: string): [string, string][] {
  const tags: [string, string][] = [];
  const start = /<([A-Za-z][\w.]*)/g;
  let match: RegExpExecArray | null;
  while ((match = start.exec(source)) !== null) {
    let depth = 0;
    let index = start.lastIndex;
    while (index < source.length) {
      const char = source[index];
      if (char === '{') depth += 1;
      else if (char === '}') depth -= 1;
      else if (char === '>' && depth === 0) break;
      index += 1;
    }
    tags.push([match[1], source.slice(start.lastIndex, index)]);
  }
  return tags;
}

const files = ROOTS.flatMap((root) => walk(root)).map((path) => [path, readFileSync(path, 'utf8')] as const);

describe('non-hover rule (V25)', () => {
  it('puts no native `title=` on a DOM element or a MUI primitive', () => {
    const offenders: string[] = [];
    for (const [path, source] of files) {
      if ([...NATIVE_TITLE_ALLOWED].some((allowed) => path.endsWith(allowed))) continue;
      const mui = muiImports(source);
      for (const [tag, attrs] of openingTags(source)) {
        const rendersAttribute =
          /^[a-z]/.test(tag) || (mui.has(tag) && !MUI_TITLE_IS_A_PROP.has(tag));
        if (!rendersAttribute) continue;
        if (/(^|\s)title=/.test(attrs)) offenders.push(`${path}: <${tag}>`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it('adds no `tabIndex` to an element that is not a control', () => {
    const offenders: string[] = [];
    for (const [path, source] of files) {
      for (const [tag, attrs] of openingTags(source)) {
        if (!/tabIndex=\{?0/.test(attrs)) continue;
        // A hand-built control says what it is and answers the keyboard; a tab
        // stop added to reach a hover does neither.
        if (/(^|\s)role=/.test(attrs) && /onKeyDown=/.test(attrs)) continue;
        offenders.push(`${path}: <${tag}>`);
      }
    }
    expect(offenders).toEqual([]);
  });

  it('actually reads the admin tree, so the guard cannot pass on an empty sweep', () => {
    // A guard that finds no file is green forever. Both halves are pinned: the
    // walk reaches the files, and the scanner recognises what it looks for.
    expect(files.length).toBeGreaterThan(40);
    expect(openingTags('<Chip size="small" title={t.hint} />')).toContainEqual([
      'Chip',
      ' size="small" title={t.hint} /',
    ]);
    // And the import reader, on both shapes — this is what makes the check
    // exhaustive instead of a list of primitives someone has to remember.
    const names = muiImports("import { Alert, Box, FormControlLabel } from '@mui/material';\nimport Button from '@mui/material/Button';");
    expect([...names].sort()).toEqual(['Alert', 'Box', 'Button', 'FormControlLabel']);
    expect(MUI_TITLE_IS_A_PROP.has('Alert')).toBe(false);
  });
});
