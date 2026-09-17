import type { Embedder } from "./embedding/embedder.js";
import { LensError } from "./errors.js";
import type { CorpusIndex } from "./index/corpusIndex.js";
import { rank, type Hit } from "./search.js";

export interface QueryOptions {
    top?: number | undefined;
    /** Collapse editions of the same text into one hit. Default true. */
    distinct?: boolean | undefined;
}
import type { ThemeCatalog } from "./themes.js";
import type { UsageLedger } from "./usage/ledger.js";

export const DEFAULT_TOP = 12;
export const MAX_TOP = 100;
/** Bounds the cost of one query; the theme queries run ~1,000 characters. */
export const MAX_QUERY_CHARS = 4_000;

export interface LensDeps {
    index: CorpusIndex;
    themes: ThemeCatalog;
    embedder: Embedder;
    ledger: UsageLedger;
    /** $ per 1M input tokens. */
    dollarsPerMTokens: number;
    /** See RankOptions.editionSimilarity. */
    editionSimilarity: number;
}

/**
 * The three read-only operations, transport-free. Order of events for a
 * query: validate → admit against the ceilings → embed → rank → record.
 * It retrieves and renders SOURCE TEXT only; it drafts no claim.
 */
export class LensService {
    constructor(private readonly deps: LensDeps) {}

    listThemes(): string[] {
        return this.deps.themes.names();
    }

    corpusSearch(query: string, opts: QueryOptions, caller: string, signal?: AbortSignal): Promise<Hit[]> {
        return this.run("corpus_search", query, opts, caller, signal);
    }

    themeLens(theme: string, opts: QueryOptions, caller: string, signal?: AbortSignal): Promise<Hit[]> {
        const t = this.deps.themes.get(theme); // unknown theme refuses before anything is spent
        return this.run("theme_lens", t.query, opts, caller, signal);
    }

    private async run(tool: string, query: string, opts: QueryOptions, caller: string, signal?: AbortSignal): Promise<Hit[]> {
        const q = query.trim();
        if (!q) throw new LensError("BAD_QUERY", "an empty query retrieves nothing");
        if (q.length > MAX_QUERY_CHARS) {
            throw new LensError("BAD_QUERY", `the query is ${q.length} characters; the limit is ${MAX_QUERY_CHARS}`);
        }
        const k = opts.top ?? DEFAULT_TOP;
        if (!Number.isInteger(k) || k < 1 || k > MAX_TOP) {
            throw new LensError("BAD_QUERY", `top must be a whole number from 1 to ${MAX_TOP}`);
        }

        const { ledger, embedder, index, dollarsPerMTokens, editionSimilarity } = this.deps;
        ledger.admit(caller);
        const t0 = performance.now();
        const elapsed = () => Math.round(performance.now() - t0) / 1000;
        try {
            const e = await embedder.embed(q, signal);
            const hits = rank(index, e.vector, k, { distinct: opts.distinct ?? true, editionSimilarity });
            ledger.record({
                caller,
                tool,
                status: "ok",
                input_tokens: e.tokens,
                cost: Math.round(e.tokens * dollarsPerMTokens) / 1e6,
                cached: e.cached,
                elapsed_s: elapsed(),
            });
            return hits;
        } catch (err) {
            const name = err instanceof Error ? err.name : "Error";
            ledger.record({ caller, tool, status: `error:${name}`, input_tokens: 0, cost: 0, cached: false, elapsed_s: elapsed() });
            if (err instanceof LensError) throw err;
            // The upstream detail goes to the operator's log; the caller gets the short of it.
            console.error(`[corpus-lens] embedding failed for ${caller}: ${(err as Error).message}`);
            const status = (err as { status?: unknown }).status;
            const detail = typeof status === "number" ? `HTTP ${status}` : (err as Error).message.slice(0, 200);
            throw new LensError(
                "EMBEDDING_FAILED",
                `the embedding engine could not be reached (${name}: ${detail}). ` +
                    "Nothing was retrieved — this tool never pretends with lexical results.",
                { cause: err },
            );
        }
    }
}
