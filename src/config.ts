import { parseArgs } from "node:util";
import { z } from "zod";
import { LensError } from "./errors.js";

const ConfigSchema = z.object({
    transport: z.enum(["stdio", "http"]).default("stdio"),
    host: z.string().default("127.0.0.1"),
    port: z.coerce.number().int().min(1).max(65535).default(8765),
    /** Hostnames the reverse proxy forwards as Host:, for DNS-rebinding protection. */
    allowedHosts: z.string().optional().transform((s) => s?.split(",").map((h) => h.trim()).filter(Boolean)),
    cacheDir: z.string().min(1, "set --cache-dir or CORPUS_CACHE_DIR"),
    themes: z.string().min(1, "set --themes or CORPUS_THEMES"),
    usageLog: z.string().min(1, "set --usage-log or CORPUS_USAGE_LOG"),
    /** If set, startup verifies cache/ and themes/ against <dir>/MANIFEST.json. */
    verifyBundle: z.string().optional(),
    /**
     * `name:token,name:token` — see TokenRegistry. Environment only. Required
     * for the http transport unless allowAnonymous is set.
     */
    apiTokens: z.string().optional(),
    /** Serve http with no authentication. For a loopback-only development machine. */
    allowAnonymous: z.enum(["true", "false"]).default("false").transform((v) => v === "true"),
    /** The caller name for stdio and for anonymous http. */
    defaultCaller: z.string().default("shared"),
    perCallerDaily: z.coerce.number().int().positive().default(200),
    dollarsDaily: z.coerce.number().positive().default(1.0),
    dollarsPerMTokens: z.coerce.number().nonnegative().default(2.0),
    /** Cosine similarity at which passages from different documents count as editions of one text. */
    editionSimilarity: z.coerce.number().gt(0).max(1).default(0.95),
    /** Never a CLI flag: flags show up in `ps`. */
    apiKey: z.string().min(1, "set GOOGLE_API_KEY (or GEMINI_API_KEY) in the environment"),
});

export type Config = z.infer<typeof ConfigSchema>;

export function loadConfig(argv: string[], env: NodeJS.ProcessEnv): Config {
    const { values: a } = parseArgs({
        args: argv,
        options: {
            transport: { type: "string" },
            host: { type: "string" },
            port: { type: "string" },
            "allowed-hosts": { type: "string" },
            "cache-dir": { type: "string" },
            themes: { type: "string" },
            "usage-log": { type: "string" },
            "verify-bundle": { type: "string" },
            "allow-anonymous": { type: "boolean" },
            caller: { type: "string" },
            "per-caller-daily": { type: "string" },
            "dollars-daily": { type: "string" },
            "dollars-per-m-tokens": { type: "string" },
            "edition-similarity": { type: "string" },
        },
    });

    const result = ConfigSchema.safeParse({
        transport: a.transport ?? env.CORPUS_TRANSPORT,
        host: a.host ?? env.CORPUS_HOST,
        port: a.port ?? env.CORPUS_PORT,
        allowedHosts: a["allowed-hosts"] ?? env.CORPUS_ALLOWED_HOSTS,
        cacheDir: a["cache-dir"] ?? env.CORPUS_CACHE_DIR ?? "",
        themes: a.themes ?? env.CORPUS_THEMES ?? "",
        usageLog: a["usage-log"] ?? env.CORPUS_USAGE_LOG ?? "",
        verifyBundle: a["verify-bundle"] ?? env.CORPUS_VERIFY_BUNDLE,
        apiTokens: env.CORPUS_API_TOKENS,
        allowAnonymous: a["allow-anonymous"] ? "true" : env.CORPUS_ALLOW_ANONYMOUS,
        defaultCaller: a.caller ?? env.CORPUS_MCP_CALLER,
        perCallerDaily: a["per-caller-daily"] ?? env.CORPUS_PER_CALLER_DAILY,
        dollarsDaily: a["dollars-daily"] ?? env.CORPUS_DOLLARS_DAILY,
        dollarsPerMTokens: a["dollars-per-m-tokens"] ?? env.CORPUS_DOLLARS_PER_M_TOKENS,
        editionSimilarity: a["edition-similarity"] ?? env.CORPUS_EDITION_SIMILARITY,
        apiKey: env.GOOGLE_API_KEY ?? env.GEMINI_API_KEY ?? "",
    });
    if (!result.success) {
        const why = result.error.issues.map((i) => `${i.path.join(".")}: ${i.message}`).join("; ");
        throw new LensError("CONFIG_INVALID", `configuration is incomplete — ${why}`);
    }
    const cfg = result.data;
    if (cfg.transport === "http" && !cfg.apiTokens && !cfg.allowAnonymous) {
        throw new LensError(
            "CONFIG_INVALID",
            "the http transport needs CORPUS_API_TOKENS (name:token,…) — or --allow-anonymous on a development machine",
        );
    }
    return cfg;
}
