export interface AccessEnv {
  TEAM_DOMAIN?: string;
  POLICY_AUD?: string;
}

export type AccessIdentity = {
  email: string;
  subject: string;
};

const TEAM_DOMAIN_PATTERN = /^https:\/\/[a-z0-9-]+\.cloudflareaccess\.com$/;

const b64url = (value: string) => {
  const normalized = value.replace(/-/g, "+").replace(/_/g, "/");
  const padded = normalized + "=".repeat((4 - (normalized.length % 4)) % 4);
  const binary = atob(padded);
  return Uint8Array.from(binary, c => c.charCodeAt(0));
};

const decodeJson = <T>(part: string): T =>
  JSON.parse(new TextDecoder().decode(b64url(part))) as T;

export async function verifyAccessRequest(
  request: Request,
  env: AccessEnv
): Promise<AccessIdentity> {
  const teamDomain = (env.TEAM_DOMAIN || "").replace(/\/$/, "");
  const audience = env.POLICY_AUD || "";
  // The issuer claim is compared to this value verbatim and the JWKS URL is
  // built from it, so it must be exactly a Cloudflare Access team origin.
  if (!TEAM_DOMAIN_PATTERN.test(teamDomain) || !audience) throw new Error("ACCESS_NOT_CONFIGURED");

  const token = request.headers.get("cf-access-jwt-assertion") || "";
  const parts = token.split(".");
  if (parts.length !== 3 || token.length > 8192) throw new Error("ACCESS_TOKEN_MISSING");

  let header: { alg?: string; kid?: string };
  let payload: {
    iss?: string;
    aud?: string | string[];
    exp?: number;
    nbf?: number;
    email?: string;
    sub?: string;
    type?: string;
  };
  try {
    header = decodeJson(parts[0]);
    payload = decodeJson(parts[1]);
  } catch {
    throw new Error("ACCESS_TOKEN_MALFORMED");
  }

  if (header.alg !== "RS256" || !header.kid) throw new Error("ACCESS_TOKEN_INVALID_HEADER");
  if (payload.iss !== teamDomain) throw new Error("ACCESS_TOKEN_INVALID_ISSUER");

  const audiences = Array.isArray(payload.aud) ? payload.aud : [payload.aud || ""];
  if (!audiences.includes(audience)) throw new Error("ACCESS_TOKEN_INVALID_AUDIENCE");

  const now = Math.floor(Date.now() / 1000);
  if (typeof payload.exp !== "number" || payload.exp <= now) throw new Error("ACCESS_TOKEN_EXPIRED");
  if (payload.nbf && payload.nbf > now + 30) throw new Error("ACCESS_TOKEN_NOT_YET_VALID");
  if (payload.type !== "app") throw new Error("ACCESS_TOKEN_INVALID_TYPE");
  if (!payload.email || !payload.sub) throw new Error("ACCESS_IDENTITY_MISSING");

  let jwks: { keys?: JsonWebKey[] };
  try {
    const jwksResponse = await fetch(`${teamDomain}/cdn-cgi/access/certs`, {
      cf: { cacheTtl: 300, cacheEverything: true },
    } as RequestInit);
    if (!jwksResponse.ok) throw new Error("status");
    jwks = await jwksResponse.json<{ keys?: JsonWebKey[] }>();
  } catch {
    throw new Error("ACCESS_JWKS_UNAVAILABLE");
  }
  const jwk = (jwks.keys || []).find((k: any) => k.kid === header.kid && k.kty === "RSA");
  if (!jwk) throw new Error("ACCESS_SIGNING_KEY_NOT_FOUND");

  let valid = false;
  try {
    const key = await crypto.subtle.importKey(
      "jwk",
      jwk,
      { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
      false,
      ["verify"]
    );
    const data = new TextEncoder().encode(`${parts[0]}.${parts[1]}`);
    valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, b64url(parts[2]), data);
  } catch {
    throw new Error("ACCESS_TOKEN_MALFORMED");
  }
  if (!valid) throw new Error("ACCESS_SIGNATURE_INVALID");

  return { email: payload.email.toLowerCase(), subject: payload.sub };
}
