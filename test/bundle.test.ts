/**
 * Runs against a real bundle when CORPUS_BUNDLE_DIR points at one; skipped
 * otherwise. No API key is needed: the "query" is a corpus vector, so the
 * passage it came from must come back first with a score of 1.
 */
import { mkdtemp } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { InMemoryTransport } from "@modelcontextprotocol/sdk/inMemory.js";
import { beforeAll, describe, expect, it } from "vitest";
import { GEMINI_EMBED_MODEL } from "../src/embedding/gemini.js";
import { compareChronological, loadCorpusIndex, verifyBundle, type CorpusIndex } from "../src/index/corpusIndex.js";
import { LensService } from "../src/lens.js";
import { buildMcpServer } from "../src/mcp/server.js";
import { rank } from "../src/search.js";
import { ThemeCatalog } from "../src/themes.js";
import { UsageLedger } from "../src/usage/ledger.js";
import { FakeEmbedder } from "./helpers.js";

const dir = process.env.CORPUS_BUNDLE_DIR;

describe.skipIf(!dir)("real bundle", () => {
    let index: CorpusIndex;
    let themes: ThemeCatalog;
    const vectorOf = (row: number) => Array.from(index.vectors.subarray(row * index.dim, (row + 1) * index.dim));

    beforeAll(async () => {
        index = await loadCorpusIndex(join(dir!, "cache"), GEMINI_EMBED_MODEL);
        themes = await ThemeCatalog.load(join(dir!, "themes", "Theme Descriptions.txt"));
    });

    it("matches MANIFEST.json", async () => {
        expect(await verifyBundle(dir!)).toEqual([]);
    });

    it("loads every passage and theme", () => {
        expect([index.fileCount, index.passages.length, index.dim]).toEqual([2999, 62508, 768]);
        expect(themes.names()).toHaveLength(10);
        expect(themes.get("The Godhead").query).toMatch(/^The divine persons themselves/);
    });

    it("refuses an index made with another model", async () => {
        await expect(loadCorpusIndex(join(dir!, "cache"), "some-other-model")).rejects.toThrow(/vectors were made with/);
    });

    it("finds a passage from its own vector, in chronological order, fast", () => {
        const row = 40_000;
        const t0 = performance.now();
        const hits = rank(index, vectorOf(row), 12, { distinct: false, editionSimilarity: 0.95 });
        const ms = performance.now() - t0;
        // Other editions of the same text share its vector exactly, so "first" is "among those scoring 1".
        const perfect = hits.filter((h) => h.score === 1).map((h) => h.stem);
        expect(perfect).toContain(index.passages[row]!.stem);
        expect(hits.find((h) => h.rank === 1)!.score).toBe(1);
        const asPassages = hits.map((h) => index.passages.find((p) => p.stem === h.stem && p.snippet === h.snippet)!);
        expect([...asPassages].sort(compareChronological)).toEqual(asPassages);
        console.log(`rank over ${index.passages.length} passages: ${ms.toFixed(1)} ms`);
        expect(ms).toBeLessThan(500);
    });

    it("collapses the editions of D&C 76:99 into one hit of twelve distinct texts", () => {
        const hits = rank(index, vectorOf(40_000), 12, { distinct: true, editionSimilarity: 0.95 });
        expect(hits).toHaveLength(12);
        const v99 = hits.find((h) => h.rank === 1)!;
        expect([v99.stem, v99.unit]).toEqual(["1832-02-16-D&C-76-RB1", "99"]); // the earliest edition leads
        expect(v99.also_in.map((e) => e.stem)).toEqual(
            expect.arrayContaining(["1835-02-01-D&C-76-EMS", "1835-08-17-D&C-76-DC1835", "1844-06-27-D&C-76-DC1844"]),
        );
        const everyone = hits.flatMap((h) => [`${h.stem}#${h.unit}`, ...h.also_in.map((e) => `${e.stem}#${e.unit}`)]);
        expect(new Set(everyone).size).toBe(everyone.length); // no passage appears twice
    });

    it("serves all three tools over MCP", async () => {
        const ledger = await UsageLedger.open(join(await mkdtemp(join(tmpdir(), "lens-")), "u.jsonl"), "fake", {
            perCallerDaily: 5,
            dollarsDaily: 1,
        });
        const lens = new LensService({
            index,
            themes,
            embedder: new FakeEmbedder(index.dim, () => vectorOf(123)),
            ledger,
            dollarsPerMTokens: 2,
            editionSimilarity: 0.95,
        });
        const server = buildMcpServer(lens, "test", "0.0.0");
        const [a, b] = InMemoryTransport.createLinkedPair();
        const client = new Client({ name: "test", version: "0" });
        await Promise.all([server.connect(a), client.connect(b)]);

        const tools = await client.listTools();
        expect(tools.tools.map((t) => t.name).sort()).toEqual(["corpus_search", "list_themes", "theme_lens"]);
        expect(tools.tools.every((t) => t.annotations?.readOnlyHint)).toBe(true);

        const listed = await client.callTool({ name: "list_themes", arguments: {} });
        expect((listed.structuredContent as { themes: string[] }).themes).toContain("Revelation");

        const found = await client.callTool({ name: "corpus_search", arguments: { query: "anything", top: 3 } });
        expect((found.structuredContent as { hits: unknown[] }).hits).toHaveLength(3);
        expect((found.content as { text: string }[])[0]!.text).toContain("rank 1 (1.000)");

        const refused = await client.callTool({ name: "theme_lens", arguments: { theme: "Zion" } });
        expect(refused.isError).toBe(true);
        expect((refused.content as { text: string }[])[0]!.text).toMatch(/'Zion' is not a theme/);
    });
});
