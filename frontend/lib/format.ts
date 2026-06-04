// Grouped integer (Latin digits in both locales — common on modern Saudi apps and
// keeps prices instantly readable). Unit words come from the message catalog.
export const money = (n: number): string =>
  new Intl.NumberFormat("en-US", { maximumFractionDigits: 0 }).format(n);

export const pctNum = (n: number): number => Math.round(n * 100);
