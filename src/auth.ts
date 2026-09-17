import { createHash } from "node:crypto";
import { LensError } from "./errors.js";

const MIN_TOKEN_CHARS = 32;

/**
 * Bearer tokens, each bound to a caller name. The name is who the usage log
 * and the per-caller ceiling see — so one token per person means one person
 * can be measured, limited, and revoked without touching anyone else.
 *
 * Spec: comma-separated `name:token` pairs, e.g. `steve:9f2c…,eric:41ab…`.
 * Only digests are kept in memory; lookup is by digest, so comparison time
 * does not depend on how much of a guess was right.
 */
export class TokenRegistry {
    private constructor(private readonly callerByDigest: ReadonlyMap<string, string>) {}

    static parse(spec: string): TokenRegistry {
        const bad = (why: string) => new LensError("CONFIG_INVALID", `CORPUS_API_TOKENS: ${why}`);
        const byDigest = new Map<string, string>();
        const names = new Set<string>();
        for (const entry of spec.split(",").map((e) => e.trim()).filter(Boolean)) {
            const colon = entry.indexOf(":");
            if (colon < 1) throw bad("each entry must be name:token");
            const name = entry.slice(0, colon).trim();
            const token = entry.slice(colon + 1).trim();
            // Never echo any part of a token into an error or a log.
            if (!/^[\w.@-]+$/.test(name)) throw bad(`'${name}' is not a usable caller name (letters, digits, . _ @ -)`);
            if (token.length < MIN_TOKEN_CHARS) throw bad(`the token for ${name} is shorter than ${MIN_TOKEN_CHARS} characters — generate one with: openssl rand -hex 32`);
            if (names.has(name)) throw bad(`${name} appears twice`);
            const d = digest(token);
            if (byDigest.has(d)) throw bad(`${name} shares a token with ${byDigest.get(d)} — every caller needs their own`);
            names.add(name);
            byDigest.set(d, name);
        }
        if (byDigest.size === 0) throw bad("no tokens found");
        return new TokenRegistry(byDigest);
    }

    get callers(): string[] {
        return [...this.callerByDigest.values()];
    }

    /** The caller a request's Authorization header proves, or undefined. */
    identify(authorization: string | undefined): string | undefined {
        const m = /^Bearer\s+(\S+)\s*$/i.exec(authorization ?? "");
        return m ? this.callerByDigest.get(digest(m[1]!)) : undefined;
    }
}

function digest(token: string): string {
    return createHash("sha256").update(token).digest("hex");
}
