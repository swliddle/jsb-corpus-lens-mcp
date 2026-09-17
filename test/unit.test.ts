import { mkdtemp, readFile, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { CachedEmbedder } from "../src/embedding/cached.js";
import { LensError } from "../src/errors.js";
import { compareChronological, dateKeyOf } from "../src/index/corpusIndex.js";
import { readNpyFloat32Matrix } from "../src/index/npy.js";
import { LensService } from "../src/lens.js";
import type { AddressInfo } from "node:net";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { TokenRegistry } from "../src/auth.js";
import { startHttp } from "../src/mcp/http.js";
import { callerFrom } from "../src/mcp/server.js";
import { rank, render } from "../src/search.js";
import { parseThemes, ThemeCatalog } from "../src/themes.js";
import { UsageLedger } from "../src/usage/ledger.js";
import { FakeEmbedder, tinyIndex } from "./helpers.js";

const tmp = () => mkdtemp(join(tmpdir(), "lens-"));

function npy(shape: string, values: number[], descr = "<f4"): Buffer {
    let header = `{'descr': '${descr}', 'fortran_order': False, 'shape': ${shape}, }`;
    header = header.padEnd(118 - 1) + "\n";
    const pre = Buffer.alloc(10);
    Buffer.from([0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59, 1, 0]).copy(pre);
    pre.writeUInt16LE(header.length, 8);
    return Buffer.concat([pre, Buffer.from(header, "latin1"), Buffer.from(new Float32Array(values).buffer)]);
}

describe("npy", () => {
    it("reads a 2-D float32 matrix", async () => {
        const p = join(await tmp(), "m.npy");
        await writeFile(p, npy("(2, 3)", [1, 2, 3, 4, 5, 6]));
        const m = await readNpyFloat32Matrix(p);
        expect([m.rows, m.cols, [...m.data]]).toEqual([2, 3, [1, 2, 3, 4, 5, 6]]);
    });
    it("refuses other dtypes and torn files", async () => {
        const d = await tmp();
        await writeFile(join(d, "a.npy"), npy("(1, 2)", [1, 2], "<f8"));
        await writeFile(join(d, "b.npy"), npy("(5, 2)", [1, 2]));
        await expect(readNpyFloat32Matrix(join(d, "a.npy"))).rejects.toThrow(/dtype/);
        await expect(readNpyFloat32Matrix(join(d, "b.npy"))).rejects.toThrow(/data bytes/);
    });
});

describe("chronology", () => {
    it("derives dates from stems, including circa and undated", () => {
        expect(dateKeyOf("1823-09-21-01-JS-History")).toBe("1823-09-21");
        expect(dateKeyOf("1820-04-FV-Integrated-Timeline")).toBe("1820-04-00");
        expect(dateKeyOf("ca-1830-04-01-D&C-20")).toBe("1830-04-01");
        expect(dateKeyOf("D&C-All-Textual-Changes")).toBe("9999-99-99");
    });
    it("orders by date, then document, then reading order — never by label text", () => {
        const idx = tinyIndex([
            { stem: "1844-01-01-late", unit: "1", ordinal: 0, vec: [1, 0] },
            { stem: "ca-1830-04-01-D&C-20", unit: "10", ordinal: 9, vec: [1, 0] },
            { stem: "ca-1830-04-01-D&C-20", unit: "2", ordinal: 1, vec: [1, 0] },
            { stem: "Undated", unit: "1", ordinal: 0, vec: [1, 0] },
        ]);
        const sorted = [...idx.passages].sort(compareChronological).map((p) => `${p.stem}#${p.unit}`);
        expect(sorted).toEqual(["ca-1830-04-01-D&C-20#2", "ca-1830-04-01-D&C-20#10", "1844-01-01-late#1", "Undated#1"]);
    });
});

describe("rank", () => {
    const idx = tinyIndex([
        { stem: "1830-01-01-a", unit: "1", ordinal: 0, vec: [1, 0, 0] },
        { stem: "1829-01-01-b", unit: "1", ordinal: 0, vec: [0.9, 0.1, 0] },
        { stem: "1831-01-01-c", unit: "1", ordinal: 0, vec: [0, 1, 0] },
        { stem: "1828-01-01-d", unit: "1", ordinal: 0, vec: [0, 0, 5] },
    ]);
    const raw = { distinct: false, editionSimilarity: 0.95 }; // ranking alone; editions are tested below
    it("takes the nearest by cosine and renders them chronologically with their rank", () => {
        const hits = rank(idx, [2, 0, 0], 2, raw);
        expect(hits.map((h) => [h.stem, h.rank])).toEqual([["1829-01-01-b", 2], ["1830-01-01-a", 1]]);
        expect(hits[1]!.score).toBe(1);
    });
    it("is unaffected by vector magnitude and caps top at the corpus size", () => {
        expect(rank(idx, [0, 0, 0.001], 1, raw)[0]!.stem).toBe("1828-01-01-d");
        expect(rank(idx, [1, 1, 1], 99, raw)).toHaveLength(4);
    });
    it("refuses a query of the wrong dimension", () => {
        expect(() => rank(idx, [1, 0], 1)).toThrow(LensError);
    });
});

describe("editions", () => {
    // Three editions of one verse (near-identical vectors), its neighbour verse in two of them, and an unrelated text.
    const idx = tinyIndex([
        { stem: "1835-08-17-D&C-90-DC1835", unit: "14", ordinal: 13, vec: [1, 0.02, 0] },
        { stem: "1833-03-08-D&C-90-RB1", unit: "14", ordinal: 13, vec: [1, 0.05, 0] },
        { stem: "1844-06-27-D&C-90-DC1844", unit: "14", ordinal: 13, vec: [1, 0.03, 0] },
        { stem: "1833-03-08-D&C-90-RB1", unit: "15", ordinal: 14, vec: [0.8, 0.6, 0] },
        { stem: "1835-08-17-D&C-90-DC1835", unit: "15", ordinal: 14, vec: [0.8, 0.61, 0] },
        { stem: "1836-03-27-D&C-109", unit: "11", ordinal: 10, vec: [0.5, 0, 0.85] },
    ]);
    const opts = { distinct: true, editionSimilarity: 0.95 };

    it("gives one hit per text: the earliest edition, the others in also_in, chronological", () => {
        const hits = rank(idx, [1, 0, 0], 3, opts);
        expect(hits.map((h) => [h.stem, h.unit, h.rank, h.also_in.map((e) => e.stem)])).toEqual([
            ["1833-03-08-D&C-90-RB1", "14", 1, ["1835-08-17-D&C-90-DC1835", "1844-06-27-D&C-90-DC1844"]],
            ["1833-03-08-D&C-90-RB1", "15", 2, ["1835-08-17-D&C-90-DC1835"]],
            ["1836-03-27-D&C-109", "11", 3, []],
        ]);
        expect(render(hits, "h")).toContain("also in: 1835-08-17-D&C-90-DC1835 · 14 (1.000); 1844-06-27-D&C-90-DC1844 · 14 (1.000)");
    });

    it("distinct:false returns every edition as its own hit", () => {
        const hits = rank(idx, [1, 0, 0], 3, { ...opts, distinct: false });
        expect(hits.map((h) => h.unit)).toEqual(["14", "14", "14"]);
        expect(hits.every((h) => h.also_in.length === 0)).toBe(true);
    });

    it("never merges two passages of the same document, however alike", () => {
        const harmony = tinyIndex([
            { stem: "1820-04-FV-Timeline", unit: "7", ordinal: 6, vec: [1, 0.01] },
            { stem: "1820-04-FV-Timeline", unit: "8", ordinal: 7, vec: [1, 0.02] },
        ]);
        expect(rank(harmony, [1, 0], 2, opts).map((h) => h.unit)).toEqual(["7", "8"]);
    });

    it("honours the threshold", () => {
        expect(rank(idx, [1, 0, 0], 6, { distinct: true, editionSimilarity: 0.999999 })).toHaveLength(6);
        expect(rank(idx, [1, 0, 0], 6, opts)).toHaveLength(3);
    });
});

const THEMES = `Intro text

1. The Godhead — About the Godhead.

   Definition: The divine persons.

   Boundary:
   - Central subject: x
   - Owns: membership and nature.

2. Mankind — About mankind, no definition line.
`;

describe("themes", () => {
    it("composes the query from Definition (or description) + Owns", () => {
        const [a, b] = parseThemes(THEMES);
        expect(a!.query).toBe("The divine persons. membership and nature.");
        expect(b!.query).toBe("About mankind, no definition line.");
    });
    it("looks up forgivingly, refuses unknown themes by name", () => {
        const cat = new ThemeCatalog(parseThemes(THEMES));
        expect(cat.get("  the godhead ").number).toBe(1);
        expect(() => cat.get("Zion")).toThrow(/'Zion' is not a theme.*The Godhead, Mankind/);
    });
});

describe("ledger", () => {
    const ceilings = { perCallerDaily: 2, dollarsDaily: 0.01 };
    const ok = (caller: string, cost: number) =>
        ({ caller, tool: "t", status: "ok", input_tokens: 1, cost, cached: false, elapsed_s: 0 }) as const;

    it("enforces both ceilings, refunds failures, and survives a restart", async () => {
        const path = join(await tmp(), "sub", "usage.jsonl");
        let l = await UsageLedger.open(path, "m", ceilings);
        l.admit("ann");
        l.record({ ...ok("ann", 0), status: "error:Timeout" });
        l.admit("ann");
        l.record(ok("ann", 0.004));
        l.admit("ann");
        l.record(ok("ann", 0.004));
        expect(() => l.admit("ann")).toThrow(/ann has reached the per-caller/);
        await l.flush();
        expect((await readFile(path, "utf8")).trim().split("\n")).toHaveLength(3);

        l = await UsageLedger.open(path, "m", ceilings); // restart: counters come back from the log
        expect(l.usage("ann")).toEqual({ queries: 2, dollars: 0.008 });
        l.admit("bob");
        l.record(ok("bob", 0.004));
        expect(() => l.admit("cat")).toThrow(/global daily ceiling/);
    });

    it("starts a fresh day at UTC midnight", async () => {
        let now = new Date("2026-09-17T23:59:00Z");
        const l = await UsageLedger.open(join(await tmp(), "u.jsonl"), "m", { perCallerDaily: 1, dollarsDaily: 1 }, () => now);
        l.admit("ann");
        expect(() => l.admit("ann")).toThrow();
        now = new Date("2026-09-18T00:00:01Z");
        expect(() => l.admit("ann")).not.toThrow();
    });
});

describe("lens service", () => {
    async function make() {
        const index = tinyIndex([
            { stem: "1830-01-01-a", unit: "1", ordinal: 0, vec: [1, 0] },
            { stem: "1831-01-01-b", unit: "1", ordinal: 0, vec: [0, 1] },
        ]);
        const fake = new FakeEmbedder(2, (t) => (t.includes("divine") ? [0, 1] : [1, 0]));
        const ledger = await UsageLedger.open(join(await tmp(), "u.jsonl"), "fake", { perCallerDaily: 3, dollarsDaily: 1 });
        const lens = new LensService({
            index,
            themes: new ThemeCatalog(parseThemes(THEMES)),
            embedder: new CachedEmbedder(fake),
            ledger,
            dollarsPerMTokens: 2,
            editionSimilarity: 0.95,
        });
        return { lens, fake, ledger };
    }

    it("theme_lens embeds the theme's query; repeats are served from cache at no cost", async () => {
        const { lens, fake, ledger } = await make();
        expect((await lens.themeLens("The Godhead", { top: 1 }, "ann"))[0]!.stem).toBe("1831-01-01-b");
        await lens.themeLens("the godhead", { top: 1 }, "ann");
        expect(fake.calls).toBe(1);
        expect(ledger.usage("ann")).toEqual({ queries: 2, dollars: 0.00002 });
    });

    it("refuses bad input before anything is spent", async () => {
        const { lens, fake, ledger } = await make();
        await expect(lens.corpusSearch("   ", { top: 1 }, "ann")).rejects.toThrow(/empty query/);
        await expect(lens.corpusSearch("x", { top: 0 }, "ann")).rejects.toThrow(/top must be/);
        await expect(lens.corpusSearch("x".repeat(5000), { top: 1 }, "ann")).rejects.toThrow(/limit is/);
        expect(() => lens.themeLens("Zion", {}, "ann")).toThrow(/not a theme/);
        expect([fake.calls, ledger.usage("ann").queries]).toEqual([0, 0]);
    });

    it("turns an engine failure into a named refusal and refunds the query", async () => {
        const { lens, ledger } = await make();
        const broken = new LensService({
            ...(lens as unknown as { deps: ConstructorParameters<typeof LensService>[0] }).deps,
            embedder: { model: "fake", dim: 2, embed: () => Promise.reject(new TypeError("fetch failed")) },
        });
        await expect(broken.corpusSearch("x", {}, "ann")).rejects.toThrow(/could not be reached \(TypeError: fetch failed\)/);
        expect(ledger.usage("ann").queries).toBe(0);
    });
});

describe("bearer tokens", () => {
    const A = "a".repeat(32);
    const B = "b".repeat(40);
    it("maps a presented token to its caller, and nothing else to anyone", () => {
        const reg = TokenRegistry.parse(`steve:${A}, eric@byu.edu:${B}`);
        expect(reg.callers).toEqual(["steve", "eric@byu.edu"]);
        expect(reg.identify(`Bearer ${A}`)).toBe("steve");
        expect(reg.identify(`bearer   ${B}`)).toBe("eric@byu.edu");
        for (const h of [undefined, "", A, `Basic ${A}`, `Bearer ${A}x`, `Bearer ${A} extra`]) expect(reg.identify(h)).toBeUndefined();
    });
    it("refuses weak, duplicate, or malformed entries without echoing a token", () => {
        expect(() => TokenRegistry.parse("steve:short")).toThrow(/steve is shorter than 32/);
        expect(() => TokenRegistry.parse(`steve:${A},eric:${A}`)).toThrow(/eric shares a token with steve/);
        expect(() => TokenRegistry.parse(`steve:${A},steve:${B}`)).toThrow(/steve appears twice/);
        expect(() => TokenRegistry.parse(A)).toThrow(/name:token/);
        expect(() => TokenRegistry.parse(" , ")).toThrow(/no tokens/);
        try {
            TokenRegistry.parse(`steve:${A},eric:${A}`);
        } catch (e) {
            expect((e as Error).message).not.toContain(A);
        }
    });
});

describe("http", () => {
    const A = "a".repeat(32);
    async function serve(tokens?: TokenRegistry) {
        const seen: string[] = [];
        const http = await startHttp({
            host: "127.0.0.1",
            port: 0,
            tokens,
            health: () => ({ status: "ok" }),
            newServer: () => {
                const s = new McpServer({ name: "t", version: "0" });
                s.registerTool("whoami", { description: "x" }, (extra) => {
                    seen.push(callerFrom(extra.authInfo, "fallback"));
                    return { content: [{ type: "text", text: seen.at(-1)! }] };
                });
                return s;
            },
        });
        const url = `http://127.0.0.1:${(http.address() as AddressInfo).port}/mcp`;
        const call = (headers: Record<string, string> = {}) =>
            fetch(url, {
                method: "POST",
                headers: { "Content-Type": "application/json", Accept: "application/json, text/event-stream", ...headers },
                body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/call", params: { name: "whoami", arguments: {} } }),
            });
        return { http, call, seen };
    }

    it("rejects a missing or wrong token with 401 before any tool runs", async () => {
        const { http, call, seen } = await serve(TokenRegistry.parse(`steve:${A}`));
        const none = await call();
        expect([none.status, none.headers.get("www-authenticate")]).toEqual([401, 'Bearer realm="corpus-lens"']);
        expect((await call({ Authorization: `Bearer ${"z".repeat(32)}` })).status).toBe(401);
        expect(seen).toEqual([]);
        http.close();
    });

    it("names the caller from the token — never from a header the client sends", async () => {
        const { http, call } = await serve(TokenRegistry.parse(`steve:${A}`));
        const r = await call({ Authorization: `Bearer ${A}`, "X-Forwarded-User": "mallory", "X-Caller": "mallory" });
        expect(r.status).toBe(200);
        expect(((await r.json()) as { result: { content: { text: string }[] } }).result.content[0]!.text).toBe("steve");
        http.close();
    });

    it("anonymous mode uses the fallback caller", async () => {
        const { http, call, seen } = await serve(undefined);
        expect((await call()).status).toBe(200);
        expect(seen).toEqual(["fallback"]);
        http.close();
    });
});
