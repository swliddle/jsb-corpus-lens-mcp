import type { Embedder, Embedding } from "./embedder.js";

/**
 * In-memory LRU in front of any Embedder. An embedding is a pure function of
 * (model, dim, text), so a repeat — above all the ten fixed theme queries —
 * costs nothing and needs no network. Concurrent identical requests share one
 * upstream call. Nothing is written to disk.
 */
export class CachedEmbedder implements Embedder {
    private readonly cache = new Map<string, number[]>();
    private readonly inFlight = new Map<string, Promise<Embedding>>();

    constructor(
        private readonly inner: Embedder,
        private readonly maxEntries = 512,
    ) {}

    get model(): string {
        return this.inner.model;
    }

    get dim(): number {
        return this.inner.dim;
    }

    async embed(text: string, signal?: AbortSignal): Promise<Embedding> {
        const hit = this.cache.get(text);
        if (hit) {
            this.cache.delete(text); // refresh recency
            this.cache.set(text, hit);
            return { vector: hit, tokens: 0, cached: true };
        }
        const pending = this.inFlight.get(text);
        if (pending) return pending.then((e) => ({ ...e, tokens: 0, cached: true }));

        const p = this.inner.embed(text, signal).finally(() => this.inFlight.delete(text));
        this.inFlight.set(text, p);
        const result = await p;
        this.cache.set(text, result.vector);
        if (this.cache.size > this.maxEntries) this.cache.delete(this.cache.keys().next().value!);
        return result;
    }
}
