// The `color` prop is not `sx`, kept from rotting back (issue #628).
//
// Under the installed MUI, `<Typography color="text.secondary">` is INERT. The
// component resolves its `color` through theme VARIANTS only — the simple
// palette keys built by `createSimplePaletteValueFilter` (`primary`, `error`,
// `warning`, …) and the camel-case text keys built from `theme.palette.text`
// (`textPrimary` · `textSecondary` · `textDisabled`, see
// `@mui/material/Typography/Typography.js`, the two `Object.entries` blocks of
// its `variants` array). A dotted palette path matches no variant, the prop is
// destructured out of the DOM props, and the text simply inherits its parent's
// colour. The system-props path that used to resolve `extendSxProp` is gone.
//
// Nothing catches it anywhere else: the prop's TS type ends in `| (string & {})`
// (Typography.d.ts), so the compiler accepts any string, and its runtime
// propTypes are an `oneOfType([oneOf([…]), string])` — no console warning
// either. 164 call sites across `app/src` therefore rendered at full ink
// instead of the theme's soft ink until this guard landed — 156 asking for
// `text.*` and 8 for a semantic tone, three of them computed and so invisible
// to the grep in the issue.
//
// What stays legal on purpose:
//   * `sx={{ color: 'text.secondary' }}` — `sx` DOES resolve palette paths, and
//     it is the right tool wherever a tone has no simple key (the viridian text
//     shade, `error.main` on a number);
//   * the simple keys on the `color` prop (`color="error"`, `color="warning"`
//     on a Chip or a bar), which resolve exactly as documented;
//   * any prop that is not `color` — `bgcolor`, `borderColor` and friends are
//     system props and resolve.
//
// The check reads the SOURCES rather than rendering, because the bug is
// invisible in a jsdom render too: the element renders, it just wears the wrong
// colour, and asserting a computed colour per call site would be 161 tests.

import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const ROOT = 'src';

/**
 * Components whose `color` prop goes through the variant lookup, so a dotted
 * path is inert on them. Everything here was checked against the installed
 * package rather than assumed:
 *
 *   * `Typography` and `Link` accept the same nine values, plus `inherit` on
 *     Link. Link additionally has a back-compat escape hatch — an unrecognised
 *     value is pushed into its own `sx` (`v6Colors[color] === undefined`), so a
 *     dotted path DOES still work there. It is listed anyway: relying on a
 *     deprecation shim for the one component that happens to keep it would put
 *     two spellings of the same intent in the tree.
 *   * `SvgIcon`, `Chip`, `Button`, `IconButton`, `CircularProgress`,
 *     `LinearProgress`, `Alert`, `FormLabel`, `InputLabel`, `Checkbox`,
 *     `Switch`, `Radio`, `Badge`, `Tabs`, `Tab`, `Rating`, `Slider`,
 *     `ToggleButton` take a strict union and have NO escape hatch; on those a
 *     dotted path is inert and (mostly) a type error too.
 *
 * MUI icon components (`WarningAmberIcon`, `RefreshIcon`, …) are `SvgIcon`
 * under any local name, so the check also matches every `*Icon` tag.
 */
const VARIANT_COLOR_COMPONENTS = new Set([
  'Alert',
  'Badge',
  'Button',
  'Checkbox',
  'Chip',
  'CircularProgress',
  'FormLabel',
  'Icon',
  'IconButton',
  'InputLabel',
  'LinearProgress',
  'Link',
  'Radio',
  'Rating',
  'Slider',
  'SvgIcon',
  'Switch',
  'Tab',
  'Tabs',
  'ToggleButton',
  'Typography',
]);

/**
 * A dotted palette path, in any of the three spellings the tree has carried:
 * a quoted literal (`'text.secondary'`), the same inside a ternary, and the
 * interpolated head the score breakdown used (`` `${tier}.main` ``).
 */
const DOTTED_PALETTE = /['"`][a-zA-Z]+\.[a-zA-Z]+|\$\{[^}]*\}\.[a-zA-Z]+/;

function walk(dir: string): string[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return walk(path);
    return path.endsWith('.tsx') && !path.endsWith('.test.tsx') ? [path] : [];
  });
}

/**
 * Every JSX opening tag as `[tagName, attributeText]` — the same forward scan
 * `sections/admin/nonHover.guard.test.ts` uses, and enough here for the same
 * reason: an attribute value is either a string or a braced expression, and the
 * depth counter is what keeps a `>` inside a braced ternary from ending the tag.
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

/**
 * The value of every `color=` attribute in one tag's attribute text, and
 * nothing of its neighbours — the quoted string (quotes kept) or the braced
 * expression (braces dropped, nesting respected).
 *
 * Slicing the value out first is what keeps the check honest. Reading the rest
 * of the tag along with it would trip on the very `sx={{ color: 'text.…' }}`
 * this guard promises to leave alone, and stopping at the first `}` would let
 * an expression with a nested object escape.
 */
function colorValues(attrs: string): string[] {
  const values: string[] = [];
  const attribute = /(?:^|\s)color=/g;
  while (attribute.exec(attrs) !== null) {
    const start = attribute.lastIndex;
    const opener = attrs[start];
    if (opener === '"' || opener === "'") {
      const end = attrs.indexOf(opener, start + 1);
      values.push(attrs.slice(start, end === -1 ? attrs.length : end + 1));
    } else if (opener === '{') {
      let depth = 0;
      let index = start;
      while (index < attrs.length) {
        if (attrs[index] === '{') depth += 1;
        else if (attrs[index] === '}' && (depth -= 1) === 0) break;
        index += 1;
      }
      values.push(attrs.slice(start + 1, index));
    }
  }
  return values;
}

/** Does one tag's attribute text carry a dotted palette path on `color`? */
const flags = (attrs: string): boolean => colorValues(attrs).some((value) => DOTTED_PALETTE.test(value));

/** Does this tag resolve `color` through the variant lookup? */
const usesVariantColor = (tag: string): boolean =>
  VARIANT_COLOR_COMPONENTS.has(tag) || (tag.endsWith('Icon') && /^[A-Z]/.test(tag));

const files = walk(ROOT).map((path) => [path, readFileSync(path, 'utf8')] as const);

describe('palette paths on the `color` prop', () => {
  it('passes no dotted palette path to a component that resolves `color` by variant', () => {
    const offenders: string[] = [];
    for (const [path, source] of files) {
      for (const [tag, attrs] of openingTags(source)) {
        if (!usesVariantColor(tag)) continue;
        for (const value of colorValues(attrs)) {
          if (DOTTED_PALETTE.test(value)) offenders.push(`${path}: <${tag} color=${value}>`);
        }
      }
    }
    expect(offenders).toEqual([]);
  });

  it('actually reads the SPA tree, so the guard cannot pass on an empty sweep', () => {
    // A guard that finds no file, or a pattern that recognises nothing, is
    // green forever. Both halves are pinned here.
    expect(files.length).toBeGreaterThan(100);
    expect(files.some(([path]) => path.endsWith('scoreParts.tsx'))).toBe(true);

    const offending = openingTags('<Typography variant="caption" color="text.secondary">x</Typography>');
    expect(offending[0][0]).toBe('Typography');
    expect(flags(offending[0][1])).toBe(true);

    // Every spelling the tree actually carried before the fix: the computed
    // form of the score breakdown, its interpolated twin, and one with a
    // nested object in the expression — which a `[^}]*` scan would miss.
    const bad = [
      "<Typography color={bad ? 'error.main' : 'textSecondary'}>x</Typography>",
      '<Typography color={`${tier}.main`}>x</Typography>',
      "<Typography color={pick({ a: 1 }) ? 'textPrimary' : 'error.main'}>x</Typography>",
    ];
    for (const snippet of bad) {
      expect(flags(openingTags(snippet)[0][1]), snippet).toBe(true);
    }
  });

  it('leaves `sx`, the simple keys and the other system props alone', () => {
    const legal = [
      '<Typography variant="caption" sx={{ color: \'text.secondary\' }}>x</Typography>',
      '<Typography variant="caption" color="textSecondary">x</Typography>',
      // A palette path on a NEIGHBOURING attribute of the same tag: legal, and
      // the shape a value-blind scan reports as an offence.
      '<Typography color="textSecondary" sx={{ bgcolor: \'background.paper\' }}>x</Typography>',
      '<Typography color="textDisabled" title="a.b">x</Typography>',
      '<Chip size="small" color="warning" />',
      '<LinearProgress color={color} />',
      '<Box sx={{ bgcolor: \'background.paper\' }} borderColor="divider" />',
    ];
    for (const snippet of legal) {
      for (const [, attrs] of openingTags(snippet)) {
        expect(flags(attrs), snippet).toBe(false);
      }
    }
  });

  it('only guards the components that resolve `color` by variant', () => {
    expect(usesVariantColor('Typography')).toBe(true);
    expect(usesVariantColor('WarningAmberIcon')).toBe(true);
    // A component of ours may define `color` any way it likes — including as a
    // value it forwards into `sx` — so it is not this guard's business.
    expect(usesVariantColor('WrittenGlyph')).toBe(false);
    expect(usesVariantColor('Box')).toBe(false);
  });
});
