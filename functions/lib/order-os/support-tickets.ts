// Shared helpers for support tickets. Tickets reuse support_threads and
// support_events (ops/order-os/schema.sql) plus the additive columns in
// ops/order-os/support-tickets-schema.sql.
import type { Role } from "./order-workflow";

export const TICKET_STATUSES = ["open", "waiting_customer", "waiting_staff", "resolved", "closed"] as const;
export const MAX_OPEN_TICKETS_PER_ORDER = 5;
export const MAX_MESSAGE_CHARS = 2000;

export async function sha256Hex(input: string): Promise<string> {
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(input));
  return [...new Uint8Array(digest)].map(b => b.toString(16).padStart(2, "0")).join("");
}

const ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"; // no 0/O/1/I
export function newPublicTicketId(): string {
  const bytes = crypto.getRandomValues(new Uint8Array(12));
  return "SOS-T-" + [...bytes].map(b => ALPHABET[b % ALPHABET.length]).join("");
}

export function newAccessToken(): string {
  return crypto.randomUUID() + crypto.randomUUID(); // 244 random bits, same shape as order tracking tokens
}

// Customers paste screenshots' text, phone numbers and sometimes passwords or
// OTPs. Only a redacted copy is ever stored. This is defence in depth, not a
// guarantee: staff must still never ask for credentials.
export function redactBody(input: unknown): string {
  let s = typeof input === "string" ? input.trim().slice(0, MAX_MESSAGE_CHARS) : "";
  // A credential keyword needs an explicit separator ("password is x", "OTP: 1234"),
  // so ordinary words such as "secret question" or "pass the exam" survive.
  s = s.replace(/\b(pass(?:word|code)?|otp|pin|cvv|secret|token)\b\s*(?:is|[:=-])\s*\S+/gi, "$1: [redacted]");
  s = s.replace(/\b(otp|pin|cvv)\b\s*\d{3,8}\b/gi, "$1: [redacted]");
  s = s.replace(/(পাসওয়ার্ড|ওটিপি|পিন)\s*(?:হলো|[:=-])\s*\S+/g, "$1: [redacted]");
  s = s.replace(/[\w.+-]+@[\w-]+(?:\.[\w-]+)+/g, "[email]");
  s = s.replace(/https?:\/\/\S+/gi, "[link]");
  s = s.replace(/(?:\+?[0-9০-৯][\s-]?){7,}/g, "[number]");
  return s;
}

export const isTicketStatus = (v: unknown): v is (typeof TICKET_STATUSES)[number] =>
  typeof v === "string" && (TICKET_STATUSES as readonly string[]).includes(v);

// Staff capability matrix (least privilege; widening needs CEO approval).
export const canReadTickets = (role: Role) => role !== "viewer";
export const canReplyTickets = (role: Role) => role === "owner" || role === "manager" || role === "support";
export const canSeeAllTickets = (role: Role) => role === "owner" || role === "manager" || role === "support";

// One identical answer for every way a customer lookup can fail, so ticket ids
// and tokens cannot be enumerated by comparing responses.
export const NOT_FOUND_BODY = { error: "NOT_FOUND" };
