// Re-copy the self-hosted font subsets from their @fontsource source packages
// (the devDependencies remain the provenance and update channel) and verify
// each copy byte-identically. Byte identity is load-bearing: the OFL fonts are
// redistributed verbatim — re-subsetting or re-packing would create a Modified
// Version, and Playfair Display carries a Reserved Font Name (OFL texts next
// to the files in public/fonts/). Run after an `npm update` of the packages;
// a changed file also needs the cache note in docs/reference/frontend-stack.md
// (the /fonts/ URLs are unhashed).
import { copyFileSync, readFileSync } from 'node:fs';

const FILES = {
  'eb-garamond': [
    'eb-garamond-latin-400-normal',
    'eb-garamond-latin-ext-400-normal',
    'eb-garamond-latin-400-italic',
    'eb-garamond-latin-ext-400-italic',
    'eb-garamond-latin-600-normal',
    'eb-garamond-latin-ext-600-normal',
  ],
  'playfair-display': [
    'playfair-display-latin-400-normal',
    'playfair-display-latin-ext-400-normal',
    'playfair-display-latin-500-normal',
    'playfair-display-latin-ext-500-normal',
    'playfair-display-latin-500-italic',
    'playfair-display-latin-ext-500-italic',
    'playfair-display-latin-600-normal',
    'playfair-display-latin-ext-600-normal',
    'playfair-display-latin-600-italic',
    'playfair-display-latin-ext-600-italic',
  ],
};

let n = 0;
for (const [pkg, names] of Object.entries(FILES)) {
  for (const name of names) {
    const src = new URL(`../node_modules/@fontsource/${pkg}/files/${name}.woff2`, import.meta.url);
    const dst = new URL(`../public/fonts/${name}.woff2`, import.meta.url);
    copyFileSync(src, dst);
    if (Buffer.compare(readFileSync(src), readFileSync(dst)) !== 0) {
      console.error(`MISMATCH after copy: ${name}`);
      process.exit(1);
    }
    n++;
  }
}
console.log(`fonts:sync — ${n} woff2 verbatim kopiert und verifiziert.`);
