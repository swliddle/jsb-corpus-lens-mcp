import { GoogleGenAI } from "@google/genai";
import type { Embedder, Embedding } from "./embedder.js";

export const GEMINI_EMBED_MODEL = "gemini-embedding-001";
/** Must match how the corpus was embedded — a different task type silently shifts the vector space. */
const TASK_TYPE = "SEMANTIC_SIMILARITY";

export interface GeminiEmbedderOptions {
    apiKey: string;
    dim: number;
    timeoutMs?: number;
    tries?: number;
}

export class GeminiEmbedder implements Embedder {
    readonly model = GEMINI_EMBED_MODEL;
    readonly dim: number;
    private readonly client: GoogleGenAI;
    private readonly timeoutMs: number;
    private readonly tries: number;

    constructor(opts: GeminiEmbedderOptions) {
        this.client = new GoogleGenAI({ apiKey: opts.apiKey });
        this.dim = opts.dim;
        this.timeoutMs = opts.timeoutMs ?? 15_000;
        this.tries = opts.tries ?? 3;
    }

    async embed(text: string, signal?: AbortSignal): Promise<Embedding> {
        // The Gemini API does not report tokens on the embed response, so they
        // are counted alongside it. Telemetry never blocks the tool: a failed
        // count is 0, a failed embed is the error.
        const [vector, tokens] = await Promise.all([
            this.withRetry((s) => this.embedOnce(text, s), signal),
            this.countTokens(text, signal).catch(() => 0),
        ]);
        return { vector, tokens, cached: false };
    }

    private async embedOnce(text: string, signal: AbortSignal): Promise<number[]> {
        const r = await this.client.models.embedContent({
            model: this.model,
            contents: [text],
            config: { taskType: TASK_TYPE, outputDimensionality: this.dim, abortSignal: signal },
        });
        const values = r.embeddings?.[0]?.values;
        if (!values || values.length !== this.dim) {
            throw new Error(`expected a ${this.dim}-dim embedding, received ${values?.length ?? "none"}`);
        }
        return values;
    }

    private async countTokens(text: string, signal?: AbortSignal): Promise<number> {
        const r = await this.client.models.countTokens({
            model: this.model,
            contents: text,
            config: { abortSignal: this.deadline(signal) },
        });
        return r.totalTokens ?? 0;
    }

    private deadline(signal?: AbortSignal): AbortSignal {
        const t = AbortSignal.timeout(this.timeoutMs);
        return signal ? AbortSignal.any([signal, t]) : t;
    }

    private async withRetry<T>(fn: (s: AbortSignal) => Promise<T>, signal?: AbortSignal): Promise<T> {
        let last: unknown;
        for (let i = 0; i < this.tries; i++) {
            try {
                return await fn(this.deadline(signal));
            } catch (e) {
                last = e;
                if (signal?.aborted || !isTransient(e) || i === this.tries - 1) break;
                await new Promise((r) => setTimeout(r, 500 * 2 ** i));
            }
        }
        throw last;
    }
}

/** Rate limits, server errors, timeouts and network failures are worth a retry; a bad key or bad request is not. */
function isTransient(e: unknown): boolean {
    const status = (e as { status?: unknown }).status;
    if (typeof status === "number") return status === 408 || status === 429 || status >= 500;
    return true;
}
