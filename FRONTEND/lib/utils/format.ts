/**
 * Deterministic Number & Financial Formatting for PAIMANA
 * 
 * MoSPI and Indian National Infrastructure reporting strictly operates in ₹ Crore
 * using the Indian Numbering System (Lakhs & Crores grouping: 2-2-3).
 * 
 * This module is 100% deterministic between Node.js SSR and all client browsers,
 * preventing any locale-dependent hydration mismatches (e.g. "45,53,276.37" vs "4,553,276.37").
 */

/**
 * Format a number using deterministic Indian grouping (e.g., 4553276.37 -> "45,53,276.37")
 * @param val Number or numeric string
 * @param decimals Optional decimal digits to preserve. If omitted, preserves existing decimals up to 2 places.
 */
export function formatIndianNumber(
  val: number | string | null | undefined,
  decimals?: number
): string {
  if (val === null || val === undefined) return '0';
  const num = typeof val === 'string' ? parseFloat(val) : val;
  if (isNaN(num)) return '0';

  const isNegative = num < 0;
  const absNum = Math.abs(num);

  let intPart: string;
  let decPart = '';

  if (typeof decimals === 'number') {
    const parts = absNum.toFixed(decimals).split('.');
    intPart = parts[0];
    decPart = parts[1] !== undefined && decimals > 0 ? `.${parts[1]}` : '';
  } else {
    // Keep existing precision (rounded to at most 2 decimal places to avoid floating point anomalies)
    const rounded = Math.round(absNum * 100) / 100;
    const parts = rounded.toString().split('.');
    intPart = parts[0];
    decPart = parts[1] ? `.${parts[1]}` : '';
  }

  if (intPart.length <= 3) {
    return (isNegative ? '-' : '') + intPart + decPart;
  }

  const last3 = intPart.slice(-3);
  const rest = intPart.slice(0, -3);
  const restGrouped = rest.replace(/\B(?=(\d{2})+(?!\d))/g, ',');

  return (isNegative ? '-' : '') + restGrouped + ',' + last3 + decPart;
}

/**
 * Format value with Indian grouping and ₹ prefix (e.g. 4553276.37 -> "₹45,53,276.37")
 */
export function formatCurrency(
  val: number | string | null | undefined,
  decimals?: number
): string {
  return `₹${formatIndianNumber(val, decimals)}`;
}

/**
 * Format value in ₹ Crore (e.g. 4553276.37 -> "₹45,53,276.37 Cr")
 */
export function formatCrores(
  val: number | string | null | undefined,
  decimals?: number
): string {
  return `₹${formatIndianNumber(val, decimals)} Cr`;
}

/**
 * General integer count formatting with Indian grouping (e.g. 21555 -> "21,555")
 */
export function formatCount(val: number | string | null | undefined): string {
  return formatIndianNumber(val, 0);
}
