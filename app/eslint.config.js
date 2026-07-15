// Flat ESLint config for the React 19 + TypeScript SPA. Pragmatic baseline:
// JS + typescript-eslint recommended (type-unaware, so it stays fast and needs
// no tsconfig project service), plus the react-hooks rules — the whole reason
// this gate exists (the `exhaustive-deps` suppressions in the tree are only
// meaningful once the rule actually runs). react-refresh findings are warnings.
// jsx-a11y guards the SVG-heavy custom-interaction surfaces (quiz, Tafel,
// admin canvas) against the mechanical accessibility slips a reviewer misses.
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
      ...reactHooks.configs.recommended.rules,
      ...jsxA11y.configs.recommended.rules,
      'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
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
);
