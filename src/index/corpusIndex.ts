import { createHash } from "node:crypto";
import { createReadStream } from "node:fs";
import { readFile } from "node:fs/promises";
import { join } from "node:path";
import { z } from "zod";
import { LensError } from "../errors.js";
import { readNpyFloat32Matrix } from "./npy.js";

/** The cache format this server understands. A bump upstream must fail here, loudly. */
export const SUPPORTED_FORM = 1;
export const MANIFEST_NAME = ".corpus-vectors.json";

const ManifestSchema = z.object({
    model: z.string(),
    form: z.number(),
    files: z.record(
        z.string(),
        z.object({
            hash: z.string(),
            labels: z.array(z.string()),
            snippets: z.array(z.string()),
            rows: z.array(z.number().int().nonnegative()),
        }),
    ),
});

export interface Passage {
    /** Row in the vector matrix; stable within one index build. */
    readonly row: number;
    /** Source file name without .txt — begins with the document's date when it has one. */
    readonly stem: string;
    /** The pipeline's label for the passage (verse, paragraph number…). NOT unique within a stem. */
    readonly unit: string;
    /** 0-based position within the source document — the true reading order. */
    readonly ordinal: number;
    readonly snippet: string;
    /** Sortable date derived from the stem: YYYY-MM-DD with 00 for unknown parts; "9999-99-99" when undated. */
    readonly dateKey: string;
}

export interface CorpusIndex {
    readonly model: string;
    readonly dim: number;
    readonly fileCount: number;
    /** Indexed by matrix row. */
    readonly passages: readonly Passage[];
    /** Row-major unit vectors, passages.length * dim. */
    readonly vectors: Float32Array;
}

const STEM_DATE = /^(?:ca-)?(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?(?=-|$)/;

/** "ca-1830-04-01-D&C-20" → "1830-04-01"; "1820-04-FV-…" → "1820-04-00"; undated → "9999-99-99". */
export function dateKeyOf(stem: string): string {
    const m = STEM_DATE.exec(stem);
    if (!m) return "9999-99-99";
    return `${m[1]}-${m[2] ?? "00"}-${m[3] ?? "00"}`;
}

/** Chronological, then by document, then by reading order within the document. */
export function compareChronological(a: Passage, b: Passage): number {
    if (a.dateKey !== b.dateKey) return a.dateKey < b.dateKey ? -1 : 1;
    if (a.stem !== b.stem) return a.stem < b.stem ? -1 : 1;
    return a.ordinal - b.ordinal;
}

export async function loadCorpusIndex(cacheDir: string, expectedModel: string): Promise<CorpusIndex> {
    const manifestPath = join(cacheDir, MANIFEST_NAME);
    const bad = (why: string) => new LensError("INDEX_INVALID", `corpus index at ${cacheDir}: ${why}`);

    let raw: string;
    try {
        raw = await readFile(manifestPath, "utf8");
    } catch (e) {
        throw bad(`cannot read ${MANIFEST_NAME} (${(e as Error).message})`);
    }
    const parsed = ManifestSchema.safeParse(JSON.parse(raw));
    if (!parsed.success) throw bad(`manifest has an unexpected shape: ${parsed.error.issues[0]?.message}`);
    const manifest = parsed.data;

    if (manifest.form !== SUPPORTED_FORM) {
        throw bad(`cache form ${manifest.form} is not the form this server was written for (${SUPPORTED_FORM})`);
    }
    if (manifest.model !== expectedModel) {
        throw bad(`vectors were made with ${manifest.model} but queries would be embedded with ${expectedModel}`);
    }

    const matrix = await readNpyFloat32Matrix(manifestPath + ".npy");
    const passages = new Array<Passage | undefined>(matrix.rows).fill(undefined);

    for (const [fileName, entry] of Object.entries(manifest.files)) {
        const n = entry.rows.length;
        if (entry.labels.length !== n || entry.snippets.length !== n) {
            throw bad(`${fileName}: labels/snippets/rows lengths differ`);
        }
        const stem = fileName.endsWith(".txt") ? fileName.slice(0, -4) : fileName;
        const dateKey = dateKeyOf(stem);
        for (let i = 0; i < n; i++) {
            const row = entry.rows[i]!;
            if (row >= matrix.rows) throw bad(`${fileName}: row ${row} is beyond the matrix (${matrix.rows} rows)`);
            if (passages[row]) throw bad(`row ${row} is claimed by two passages`);
            passages[row] = { row, stem, unit: entry.labels[i]!, ordinal: i, snippet: entry.snippets[i]!, dateKey };
        }
    }
    const missing = passages.findIndex((p) => p === undefined);
    if (missing !== -1) throw bad(`matrix row ${missing} has no passage — manifest and vectors do not line up`);

    normalizeRows(matrix.data, matrix.cols);
    return {
        model: manifest.model,
        dim: matrix.cols,
        fileCount: Object.keys(manifest.files).length,
        passages: passages as Passage[],
        vectors: matrix.data,
    };
}

/** In place. After this, cosine similarity is a plain dot product. Zero rows stay zero. */
export function normalizeRows(data: Float32Array, dim: number): void {
    for (let start = 0; start < data.length; start += dim) {
        let sum = 0;
        for (let j = start; j < start + dim; j++) sum += data[j]! * data[j]!;
        if (sum === 0) continue;
        const inv = 1 / Math.sqrt(sum);
        for (let j = start; j < start + dim; j++) data[j]! *= inv;
    }
}

const BundleManifestSchema = z.object({ files: z.record(z.string(), z.string()) });

/**
 * Checks the data members of a bundle against its MANIFEST.json sha256 list.
 * Only members that exist under `bundleDir` AND are data (cache/, themes/) are
 * checked — the Python sources in the bundle are not this server's concern.
 */
export async function verifyBundle(bundleDir: string): Promise<string[]> {
    const bad = (path: string, e: unknown) =>
        new LensError("INDEX_INVALID", `cannot verify the bundle — ${path} is unreadable (${(e as NodeJS.ErrnoException).code ?? (e as Error).message}); check that the service account owns the bundle directory`);
    const manifestPath = join(bundleDir, "MANIFEST.json");
    let text: string;
    try {
        text = await readFile(manifestPath, "utf8");
    } catch (e) {
        throw bad(manifestPath, e);
    }
    const m = BundleManifestSchema.parse(JSON.parse(text));
    const mismatched: string[] = [];
    for (const [member, expected] of Object.entries(m.files)) {
        if (!member.startsWith("cache/") && !member.startsWith("themes/")) continue;
        const path = join(bundleDir, member);
        const actual = await sha256File(path).catch((e) => {
            throw bad(path, e);
        });
        if (actual !== expected) mismatched.push(member);
    }
    return mismatched;
}

function sha256File(path: string): Promise<string> {
    return new Promise((resolve, reject) => {
        const h = createHash("sha256");
        createReadStream(path)
            .on("data", (c) => h.update(c))
            .on("end", () => resolve(h.digest("hex")))
            .on("error", reject);
    });
}
