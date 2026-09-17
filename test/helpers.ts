import type { Embedder, Embedding } from "../src/embedding/embedder.js";
import { dateKeyOf, normalizeRows, type CorpusIndex, type Passage } from "../src/index/corpusIndex.js";

export function tinyIndex(rows: { stem: string; unit: string; ordinal: number; vec: number[] }[]): CorpusIndex {
    const dim = rows[0]!.vec.length;
    const vectors = new Float32Array(rows.flatMap((r) => r.vec));
    normalizeRows(vectors, dim);
    const passages: Passage[] = rows.map((r, row) => ({
        row,
        stem: r.stem,
        unit: r.unit,
        ordinal: r.ordinal,
        snippet: `${r.stem} ${r.unit}`,
        dateKey: dateKeyOf(r.stem),
    }));
    return { model: "fake", dim, fileCount: new Set(rows.map((r) => r.stem)).size, passages, vectors };
}

export class FakeEmbedder implements Embedder {
    readonly model = "fake";
    calls = 0;
    constructor(
        readonly dim: number,
        private readonly fn: (text: string) => number[],
    ) {}
    async embed(text: string): Promise<Embedding> {
        this.calls++;
        return { vector: this.fn(text), tokens: 10, cached: false };
    }
}
