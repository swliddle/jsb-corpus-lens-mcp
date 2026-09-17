import { LensError } from "./errors.js";
import { compareChronological, type CorpusIndex } from "./index/corpusIndex.js";

export interface Edition {
    stem: string;
    unit: string;
    score: number;
}

export interface Hit {
    stem: string;
    unit: string;
    /** 1 = nearest in meaning. */
    rank: number;
    /** Cosine similarity, 4 decimal places. */
    score: number;
    snippet: string;
    /** Other editions of the same text (distinct mode only), chronological. The hit itself is the earliest. */
    also_in: Edition[];
}

export interface RankOptions {
    /**
     * Collapse editions of one text into a single hit. The corpus holds many
     * revelations in several editions (RB1, BoC, DC1835, DC1844…) whose
     * vectors are near-identical; left alone they fill the list with copies.
     */
    distinct: boolean;
    /**
     * Cosine similarity at or above which two passages FROM DIFFERENT
     * DOCUMENTS are one text. Measured on this corpus: editions of a verse sit
     * at a median of 0.995; neighbouring verses at 0.82 (99th percentile 0.95).
     */
    editionSimilarity: number;
}

export const DEFAULT_RANK_OPTIONS: RankOptions = { distinct: true, editionSimilarity: 0.95 };

/** In distinct mode, how far past `top` to look for editions and replacements. */
const POOL_FACTOR = 8;
const POOL_MIN = 64;

/**
 * The `top` nearest passages by cosine similarity, returned in chronological
 * reading order (each hit keeps its similarity rank). Pure and synchronous:
 * one pass over the matrix with a small sorted buffer — no full argsort.
 */
export function rank(index: CorpusIndex, query: ArrayLike<number>, top: number, options: RankOptions = DEFAULT_RANK_OPTIONS): Hit[] {
    const { dim, passages } = index;
    if (query.length !== dim) {
        throw new LensError("EMBEDDING_FAILED", `query vector has ${query.length} dims, the index has ${dim}`);
    }
    const want = Math.min(top, passages.length);
    const pool = options.distinct ? Math.min(passages.length, Math.max(want * POOL_FACTOR, POOL_MIN)) : want;
    const nearest = nearestRows(index, query, pool);

    const groups = options.distinct
        ? groupEditions(index, nearest, want, options.editionSimilarity)
        : nearest.map((n) => [n]);

    const hits = groups.map((members, i) => {
        const byDate = members
            .map((m) => ({ passage: passages[m.row]!, score: m.score }))
            .sort((a, b) => compareChronological(a.passage, b.passage));
        return { first: byDate[0]!, rest: byDate.slice(1), rank: i + 1 };
    });
    hits.sort((a, b) => compareChronological(a.first.passage, b.first.passage));

    return hits.map(({ first, rest, rank }) => ({
        stem: first.passage.stem,
        unit: first.passage.unit,
        rank,
        score: round4(first.score),
        snippet: first.passage.snippet,
        also_in: rest.map((e) => ({ stem: e.passage.stem, unit: e.passage.unit, score: round4(e.score) })),
    }));
}

interface Scored {
    row: number;
    score: number;
}

/** The `k` rows nearest the query, best first. */
function nearestRows(index: CorpusIndex, query: ArrayLike<number>, k: number): Scored[] {
    const { dim, vectors, passages } = index;
    const q = new Float32Array(dim);
    let qq = 0;
    for (let j = 0; j < dim; j++) qq += query[j]! * query[j]!;
    const inv = qq > 0 ? 1 / Math.sqrt(qq) : 1;
    for (let j = 0; j < dim; j++) q[j] = query[j]! * inv;

    const bestRow = new Int32Array(k);
    const bestScore = new Float32Array(k).fill(-Infinity);
    for (let row = 0, base = 0; row < passages.length; row++, base += dim) {
        let s = 0;
        for (let j = 0; j < dim; j++) s += vectors[base + j]! * q[j]!;
        if (s <= bestScore[k - 1]!) continue;
        let i = k - 1;
        while (i > 0 && bestScore[i - 1]! < s) {
            bestScore[i] = bestScore[i - 1]!;
            bestRow[i] = bestRow[i - 1]!;
            i--;
        }
        bestScore[i] = s;
        bestRow[i] = row;
    }
    return Array.from(bestRow, (row, i) => ({ row, score: bestScore[i]! }));
}

/**
 * Greedy, best first: a candidate joins the first group whose founding member
 * it matches — unless that group already holds a passage from the same
 * document, since two parts of one document are never editions of each other.
 * Otherwise it founds a group while fewer than `want` exist. The whole pool is
 * walked so that each group collects every edition the pool contains.
 */
function groupEditions(index: CorpusIndex, nearest: Scored[], want: number, threshold: number): Scored[][] {
    const { dim, vectors, passages } = index;
    const groups: Scored[][] = [];
    for (const c of nearest) {
        const stem = passages[c.row]!.stem;
        const home = groups.find(
            (g) => !g.some((m) => passages[m.row]!.stem === stem) && dot(vectors, g[0]!.row * dim, c.row * dim, dim) >= threshold,
        );
        if (home) home.push(c);
        else if (groups.length < want) groups.push([c]);
    }
    return groups;
}

function dot(v: Float32Array, a: number, b: number, dim: number): number {
    let s = 0;
    for (let j = 0; j < dim; j++) s += v[a + j]! * v[b + j]!;
    return s;
}

function round4(x: number): number {
    return Math.round(x * 1e4) / 1e4;
}

export function render(hits: readonly Hit[], heading: string): string {
    const lines = [heading];
    for (const h of hits) {
        lines.push(`  ${h.stem} · ${h.unit} · rank ${h.rank} (${h.score.toFixed(3)})`);
        lines.push(`     ${h.snippet}`);
        if (h.also_in.length) {
            lines.push(`     also in: ${h.also_in.map((e) => `${e.stem} · ${e.unit} (${e.score.toFixed(3)})`).join("; ")}`);
        }
    }
    return lines.join("\n");
}
