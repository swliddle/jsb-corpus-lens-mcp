#!/usr/bin/env node
import { readFileSync } from "node:fs";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { TokenRegistry } from "./auth.js";
import { loadConfig } from "./config.js";
import { CachedEmbedder } from "./embedding/cached.js";
import { GEMINI_EMBED_MODEL, GeminiEmbedder } from "./embedding/gemini.js";
import { LensError } from "./errors.js";
import { loadCorpusIndex, verifyBundle } from "./index/corpusIndex.js";
import { LensService } from "./lens.js";
import { startHttp } from "./mcp/http.js";
import { buildMcpServer } from "./mcp/server.js";
import { ThemeCatalog } from "./themes.js";
import { UsageLedger } from "./usage/ledger.js";

// stdout belongs to the stdio transport; everything human goes to stderr.
const log = (msg: string) => console.error(`[corpus-lens] ${msg}`);

async function main(): Promise<void> {
    const cfg = loadConfig(process.argv.slice(2), process.env);
    const { version } = JSON.parse(readFileSync(new URL("../package.json", import.meta.url), "utf8")) as { version: string };

    if (cfg.verifyBundle) {
        const mismatched = await verifyBundle(cfg.verifyBundle);
        if (mismatched.length) throw new LensError("INDEX_INVALID", `MANIFEST.json mismatch: ${mismatched.join(", ")}`);
        log("bundle manifest verified");
    }

    const t0 = performance.now();
    const [index, themes] = await Promise.all([loadCorpusIndex(cfg.cacheDir, GEMINI_EMBED_MODEL), ThemeCatalog.load(cfg.themes)]);
    log(
        `index loaded in ${Math.round(performance.now() - t0)} ms: ${index.fileCount} files, ` +
            `${index.passages.length} passages, ${index.dim} dims, ${themes.themes.length} themes`,
    );

    const embedder = new CachedEmbedder(new GeminiEmbedder({ apiKey: cfg.apiKey, dim: index.dim }));
    const ledger = await UsageLedger.open(cfg.usageLog, embedder.model, {
        perCallerDaily: cfg.perCallerDaily,
        dollarsDaily: cfg.dollarsDaily,
    });
    const lens = new LensService({ index, themes, embedder, ledger, dollarsPerMTokens: cfg.dollarsPerMTokens, editionSimilarity: cfg.editionSimilarity });
    const newServer = () => buildMcpServer(lens, cfg.defaultCaller, version);

    let close: () => Promise<void>;
    if (cfg.transport === "stdio") {
        const server = newServer();
        await server.connect(new StdioServerTransport());
        close = () => server.close();
        log("serving on stdio");
    } else {
        const tokens = cfg.apiTokens ? TokenRegistry.parse(cfg.apiTokens) : undefined;
        const started = Date.now();
        const http = await startHttp({
            host: cfg.host,
            port: cfg.port,
            allowedHosts: cfg.allowedHosts,
            tokens,
            newServer,
            health: () => ({
                status: "ok",
                version,
                model: index.model,
                passages: index.passages.length,
                themes: themes.themes.length,
                uptime_s: Math.round((Date.now() - started) / 1000),
            }),
        });
        close = () => new Promise((r) => http.close(() => r()));
        log(
            `serving on http://${cfg.host}:${cfg.port}/mcp — ` +
                (tokens ? `bearer tokens for: ${tokens.callers.join(", ")}` : "ANONYMOUS (no authentication)"),
        );
    }

    for (const sig of ["SIGINT", "SIGTERM"] as const) {
        process.once(sig, () => {
            log(`${sig} — shutting down`);
            void close()
                .then(() => ledger.flush())
                .finally(() => process.exit(0));
        });
    }
}

main().catch((e) => {
    log(e instanceof LensError ? `refusing to start — ${e.message}` : String((e as Error).stack ?? e));
    process.exit(1);
});
