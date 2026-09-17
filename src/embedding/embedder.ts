export interface Embedding {
    vector: number[];
    /** Input tokens billed for this call; 0 when served from cache or unknown. */
    tokens: number;
    cached: boolean;
}

/**
 * The one seam between the lens and whoever turns text into vectors. The
 * corpus vectors and every query MUST come from the same `model` — the index
 * loader enforces that against the cache manifest at startup.
 */
export interface Embedder {
    readonly model: string;
    readonly dim: number;
    embed(text: string, signal?: AbortSignal): Promise<Embedding>;
}
