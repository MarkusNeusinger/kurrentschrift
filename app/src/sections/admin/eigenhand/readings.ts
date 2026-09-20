// How the strip surface prints a measured number — and, above all, how it
// prints one that was never measured. Shared by the Befund sheet and the raw
// per-Bahn readings so that „no reading here" looks the same in both.

// „No reading here" — one dash for the whole panel, so a missing measurement
// never has to borrow a zero to have something to show.
const NO_READING = '–';

export function num(value: unknown, digits = 1): string {
  return typeof value === 'number' ? value.toFixed(digits) : NO_READING;
}

/** A counted sensor as its chip label; a sensor that was not counted reads as the panel's dash. */
export function countLabel(value: number | null): string {
  return value === null ? NO_READING : String(value);
}
