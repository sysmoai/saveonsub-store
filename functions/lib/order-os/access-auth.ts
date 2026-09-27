export interface AccessEnv {
  TEAM_DOMAIN?: string;
  POLICY_AUD?: string;
}

export type AccessIdentity = {
  email: string;
  subject: string;
};

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
  if (!teamDomain || !audience) throw new Error("ACCESS_NOT_CONFIGURED");

  const token = request.headers.get("cf-access-jwt-assertion") || "";
  const parts = token.split(".");
  if (parts.length !== 3) throw new Error("ACCESS_TOKEN_MISSING");

  const header = decodeJson<{ alg?: string; kid?: string }>(parts[0]);
  const payload = decodeJson<{
    iss?: string;
    aud?: string | string[];
    exp?: number;
    nbf?: number;
    email?: string;
    sub?: string;
    type?: string;
  }>(parts[1]);

  if (header.alg !== "RS256" || !header.kid) throw new Error("ACCESS_TOKEN_INVALID_HEADER");
  if (payload.iss !== teamDomain) throw new Error("ACCESS_TOKEN_INVALID_ISSUER");

  const audiences = Array.isArray(payload.aud) ? payload.aud : [payload.aud || ""];
  if (!audiences.includes(audience)) throw new Error("ACCESS_TOKEN_INVALID_AUDIENCE");

  const now = Math.floor(Date.now() / 1000);
  if (!payload.exp || payload.exp <= now) throw new Error("ACCESS_TOKEN_EXPIRED");
  if (payload.nbf && payload.nbf > now + 30) throw new Error("ACCESS_TOKEN_NOT_YET_VALID");
  if (payload.type && payload.type !== "app") throw new Error("ACCESS_TOKEN_INVALID_TYPE");
  if (!payload.email || !payload.sub) throw new Error("ACCESS_IDENTITY_MISSING");

  const jwksResponse = await fetch(`${teamDomain}/cdn-cgi/access/certs`, {
    cf: { cacheTtl: 300, cacheEverything: true },
  } as RequestInit);
  if (!jwksResponse.ok) throw new Error("ACCESS_JWKS_UNAVAILABLE");
  const jwks = await jwksResponse.json<{ keys?: JsonWebKey[] }>();
  const jwk = (jwks.keys || []).find((k: any) => k.kid === header.kid);
  if (!jwk) throw new Error("ACCESS_SIGNING_KEY_NOT_FOUND");

  const key = await crypto.subtle.importKey(
    "jwk",
    jwk,
    { name: "RSASSA-PKCS1-v1_5", hash: "SHA-256" },
    false,
    ["verify"]
  );

  const data = new TextEncoder().encode(`${parts[0]}.${parts[1]}`);
  const signature = b64url(parts[2]);
  const valid = await crypto.subtle.verify("RSASSA-PKCS1-v1_5", key, signature, data);
  if (!valid) throw new Error("ACCESS_SIGNATURE_INVALID");

  return { email: payload.email.toLowerCase(), subject: payload.sub };
}
