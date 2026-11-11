// Small shared validators for the lifecycle/finance endpoints (G3, G4, G6).

export const EVIDENCE_REF = /^(stmt:[A-Za-z0-9._:-]{3,120}|r2:sos\/private\/[A-Za-z0-9._\/-]{3,200})$/;

// Whole taka or paisa precision only; returns minor units or null.
export function bdtToMinor(value: unknown, { allowNegative = false } = {}): number | null {
  const n = typeof value === "number" ? value : typeof value === "string" && value.trim() ? Number(value) : NaN;
  if (!Number.isFinite(n) || n === 0) return null;
  if (!allowNegative && n < 0) return null;
  const minor = Math.round(n * 100);
  if (Math.abs(minor - n * 100) > 1e-6 || Math.abs(minor) > 100_000_000_00) return null;
  return minor;
}

// A real calendar date in YYYY-MM-DD form.
export function isIsoDate(value: unknown): value is string {
  if (typeof value !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(value)) return false;
  const d = new Date(`${value}T00:00:00Z`);
  return !Number.isNaN(d.getTime()) && d.toISOString().slice(0, 10) === value;
}

// Asia/Dhaka is UTC+6 with no DST.
const DHAKA_OFFSET_MS = 6 * 60 * 60 * 1000;
export const dhakaToday = (now = Date.now()) => new Date(now + DHAKA_OFFSET_MS).toISOString().slice(0, 10);

export function addDays(isoDate: string, days: number) {
  const d = new Date(`${isoDate}T00:00:00Z`);
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}

// Product-specific anniversary-month arithmetic for REVIEW-ONLY expiry estimates.
// Clamps dates near a month end (e.g. Jan 31 + 1 calendar month = Feb 28/29).
// Never use an estimate as provider-confirmed entitlement evidence.
export function addCalendarMonthsClamped(isoDate: string, months: number): string | null {
  if (!isIsoDate(isoDate) || !Number.isInteger(months) || months < 1 || months > 12) return null;
  const target = new Date(`${isoDate}T00:00:00Z`);
  const originalDay = target.getUTCDate();
  target.setUTCDate(1);
  target.setUTCMonth(target.getUTCMonth() + months);
  const endOfTargetMonth = new Date(target.getTime());
  endOfTargetMonth.setUTCMonth(endOfTargetMonth.getUTCMonth() + 1);
  endOfTargetMonth.setUTCDate(0);
  target.setUTCDate(Math.min(originalDay, endOfTargetMonth.getUTCDate()));
  return target.toISOString().slice(0, 10);
}

// UTC instant bounds of a Dhaka calendar month "YYYY-MM".
export function dhakaMonthBounds(month: string): { start: string; end: string } | null {
  if (!/^\d{4}-(0[1-9]|1[0-2])$/.test(month)) return null;
  const [y, m] = month.split("-").map(Number);
  const start = new Date(Date.UTC(y, m - 1, 1) - DHAKA_OFFSET_MS).toISOString();
  const end = new Date(Date.UTC(y, m, 1) - DHAKA_OFFSET_MS).toISOString();
  return { start, end };
}
