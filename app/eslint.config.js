// Flat ESLint config for the React 19 + TypeScript SPA. Pragmatic baseline:
// JS + typescript-eslint recommended (type-unaware, so it stays fast and needs
// no tsconfig project service), plus the react-hooks rules — the whole reason
// this gate exists (the `exhaustive-deps` suppressions in the tree are only
// meaningful once the rule actually runs). react-refresh findings are warnings.
// jsx-a11y guards the SVG-heavy custom-interaction surfaces (quiz, Tafel,
// admin canvas) against the mechanical accessibility slips a reviewer misses.
//
// eslint-plugin-jsx-a11y is the one plugin here whose peer range still stops at
// ESLint 9 (6.10.2 is its newest release), which is why `npm ci` refused the
// ESLint 10 bump until `package.json` gained an `overrides` entry for its peer.
// The plugin itself runs fine on 10 — verified by its rules still firing
// (`jsx-a11y/no-autofocus` on a canary file). The override names `^10.8.0`
// rather than `$eslint` on purpose: it may only claim the major this was
// actually checked against, so the next major bump fails loudly again instead
// of silently inheriting a permission nobody re-verified. Drop it as soon as
// upstream ships a release that declares ESLint 10.
import js from '@eslint/js';
import globals from 'globals';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  // designsync-entry.tsx lives outside src/tsconfig on purpose (build tool entry).
  { ignores: ['dist', 'designsync-entry.tsx'] },
  {
    files: ['**/*.{ts,tsx}'],
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    languageOptions: {
      ecmaVersion: 2022,
      globals: globals.browser,
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      'jsx-a11y': jsxA11y,
    },
    rules: {
      // eslint-plugin-react-hooks v7 folded the stabilised React Compiler rule
      // set into `recommended` — 16 rules where v5 shipped two. The preset is
      // adopted as-is, with no downgrades: `react-hooks/refs` and
      // `react-hooks/set-state-in-effect` used to sit at `warn` because the
      // tree carried 39 long-standing sites of the latest-ref render write and
      // the "reset transient state when the input prop changes" effect (issue
      // #227). Those are cleared — the resets moved into React's render-phase
      // guard, the ref writes into effects — so the preset's own severity
      // stands and the parking lot cannot be re-opened by adding to it.
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      // At `error` for the same reason: the 25 sites it found were real
      // Fast-Refresh boundaries (a provider beside its hook, a route table
      // beside the components it names), and splitting them cost one import
      // each. `npm run lint` additionally runs with `--max-warnings 0`, so a
      // rule that only warns still fails the gate.
      'react-refresh/only-export-components': ['error', { allowConstantExport: true }],
      // Honour the `_`-prefix convention for intentionally-unused bindings.
      '@typescript-eslint/no-unused-vars': [
        'error',
        { argsIgnorePattern: '^_', varsIgnorePattern: '^_', caughtErrorsIgnorePattern: '^_' },
      ],
      // German typography: non-breaking / narrow-NBSP spaces in UI strings and
      // comments are deliberate content, not stray whitespace.
      'no-irregular-whitespace': [
        'error',
        { skipStrings: true, skipComments: true, skipTemplates: true, skipJSXText: true },
      ],
    },
  },
  // The public/admin locale split (locales/index.ts vs locales/admin.ts) only
  // holds as long as no public file imports the admin barrel: one such import
  // pulls ~66 kB of admin/wizard strings (~23 kB gzipped) into the eagerly
  // loaded public bundle, and nothing except this rule would notice — the app
  // still renders identically. The extra `de/admin` / `de/wizard` patterns
  // close the relative-path bypass around the barrel, and the trailing `*`
  // closes the extensioned one (`@/locales/admin.ts` compiles here —
  // allowImportingTsExtensions — and minimatch treats it as a different
  // specifier). The `*` deliberately over-matches sibling names like a
  // hypothetical `adminHelpers`; a false positive fails loudly at lint with
  // this message, silence is the failure mode this rule exists to prevent.
  {
    files: ['src/**/*.{ts,tsx}'],
    ignores: [
      'src/pages/admin/**',
      'src/sections/admin/**',
      'src/layouts/admin/**',
      'src/locales/admin.ts',
    ],
    rules: {
      'no-restricted-imports': [
        'error',
        {
          patterns: [
            {
              group: ['@/locales/admin*', '**/locales/admin*', '**/de/admin*', '**/de/wizard*'],
              message:
                'Admin locale strings (~66 kB source, ~23 kB gz) must stay out of the public bundle. Import { de } from "@/locales" — or move this file under an admin directory if it is admin code.',
            },
          ],
        },
      ],
    },
  },
);
