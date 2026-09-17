import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import type { CallToolResult } from "@modelcontextprotocol/sdk/types.js";
import { z } from "zod";
import { LensError } from "../errors.js";
import { DEFAULT_TOP, MAX_QUERY_CHARS, MAX_TOP, type LensService } from "../lens.js";
import { render, type Hit } from "../search.js";

/**
 * Who is asking. Over http the transport has already authenticated the bearer
 * token and put the caller's name in authInfo.clientId; nothing a client sends
 * in a header is ever taken as identity. Over stdio there is only the fallback.
 */
export function callerFrom(authInfo: { clientId: string } | undefined, fallback: string): string {
    return authInfo?.clientId || fallback;
}

const READ_ONLY = { readOnlyHint: true, destructiveHint: false, idempotentHint: true, openWorldHint: false } as const;

const top = z.number().int().min(1).max(MAX_TOP).default(DEFAULT_TOP).describe("How many passages to return");

const distinct = z
    .boolean()
    .default(true)
    .describe(
        "Many texts exist in several editions. true (default): one hit per text — the earliest edition, with the others " +
            "listed in also_in. false: every edition is its own hit (for comparing textual variants).",
    );

const hitsShape = {
    hits: z.array(
        z.object({
            stem: z.string().describe("Source document; begins with its date when it has one"),
            unit: z.string().describe("Verse or paragraph label within the document"),
            rank: z.number().int().describe("1 = nearest in meaning"),
            score: z.number().describe("Cosine similarity"),
            snippet: z.string().describe("First 200 characters of the passage"),
            also_in: z
                .array(z.object({ stem: z.string(), unit: z.string(), score: z.number() }))
                .describe("Other editions of this same text, chronological; empty when distinct is false"),
        }),
    ),
};

export function buildMcpServer(lens: LensService, fallbackCaller: string, version: string): McpServer {
    const server = new McpServer(
        { name: "corpus-lens", version },
        {
            instructions:
                "Read-only retrieval over a dated corpus of Joseph Smith's revelations and accounts. " +
                "Results are passages (stem · unit · rank · score · snippet) in chronological order — " +
                "a reading list, never a claim. Snippets are truncated source text; cite the stem and unit. " +
                "Editions of one text are merged into a single hit unless distinct is false.",
        },
    );

    server.registerTool(
        "corpus_search",
        {
            title: "Search the corpus by meaning",
            description: "Passages nearest in meaning to any wording, in chronological order.",
            inputSchema: { query: z.string().min(1).max(MAX_QUERY_CHARS).describe("Any wording; matched by meaning, not keywords"), top, distinct },
            outputSchema: hitsShape,
            annotations: READ_ONLY,
        },
        ({ query, top, distinct }, extra) =>
            answer(`Nearest to “${query}”:`, () =>
                lens.corpusSearch(query, { top, distinct }, callerFrom(extra.authInfo, fallbackCaller), extra.signal),
            ),
    );

    server.registerTool(
        "theme_lens",
        {
            title: "Passages carrying a named theme",
            description:
                "Passages most likely to carry a named theme (its Definition + Owns line as the query), " +
                "in chronological order. Use list_themes for the names.",
            inputSchema: { theme: z.string().min(1).describe("A theme name exactly as list_themes gives it"), top, distinct },
            outputSchema: hitsShape,
            annotations: READ_ONLY,
        },
        ({ theme, top, distinct }, extra) =>
            answer(`${theme}:`, () => lens.themeLens(theme, { top, distinct }, callerFrom(extra.authInfo, fallbackCaller), extra.signal)),
    );

    server.registerTool(
        "list_themes",
        {
            title: "List the themes",
            description: "The theme names the lens knows.",
            outputSchema: { themes: z.array(z.string()) },
            annotations: READ_ONLY,
        },
        () => {
            const themes = lens.listThemes();
            return { content: [{ type: "text", text: themes.join("\n") }], structuredContent: { themes } };
        },
    );

    return server;
}

/** Hits go out twice: rendered text for the reader, structured for the program. A LensError is refused BY NAME over the wire. */
async function answer(heading: string, run: () => Promise<Hit[]>): Promise<CallToolResult> {
    try {
        const hits = await run();
        return { content: [{ type: "text", text: render(hits, heading) }], structuredContent: { hits } };
    } catch (e) {
        if (e instanceof LensError) return { isError: true, content: [{ type: "text", text: e.message }] };
        throw e;
    }
}
