/**
 * Drives the Desktop Extension's bridge exactly as Claude Desktop does — a
 * child process speaking MCP over stdio, configured only through the two
 * environment variables the manifest sets — against a token-protected server.
 */
import type { AddressInfo } from "node:net";
import type { Server } from "node:http";
import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { afterAll, beforeAll, describe, expect, it } from "vitest";
import { z } from "zod";
import { TokenRegistry } from "../src/auth.js";
import { startHttp } from "../src/mcp/http.js";
import { callerFrom } from "../src/mcp/server.js";

const TOKEN = "e".repeat(64);
const BRIDGE = new URL("../desktop-extension/server/index.js", import.meta.url).pathname;

let http: Server;
let url: string;

beforeAll(async () => {
    http = await startHttp({
        host: "127.0.0.1",
        port: 0,
        tokens: TokenRegistry.parse(`eric:${TOKEN}`),
        health: () => ({}),
        newServer: () => {
            const s = new McpServer({ name: "t", version: "0" });
            s.registerTool("echo", { description: "x", inputSchema: { text: z.string() } }, ({ text }, extra) => ({
                content: [{ type: "text", text: `${callerFrom(extra.authInfo, "?")} said ${text}` }],
            }));
            return s;
        },
    });
    url = `http://127.0.0.1:${(http.address() as AddressInfo).port}/mcp`;
});
afterAll(() => http.close());

async function bridge(env: Record<string, string>) {
    const client = new Client({ name: "claude-desktop-sim", version: "0" });
    await client.connect(new StdioClientTransport({ command: process.execPath, args: [BRIDGE], env, stderr: "ignore" }));
    return client;
}

describe("desktop extension bridge", () => {
    it("lists and calls tools as the token's owner", async () => {
        const c = await bridge({ CORPUS_LENS_URL: url, CORPUS_LENS_TOKEN: TOKEN });
        expect((await c.listTools()).tools.map((t) => t.name)).toEqual(["echo"]);
        const r = await c.callTool({ name: "echo", arguments: { text: "hello" } });
        expect((r.content as { text: string }[])[0]!.text).toBe("eric said hello");
        await c.close();
    });

    it("forgives a token pasted with whitespace or a Bearer prefix", async () => {
        const c = await bridge({ CORPUS_LENS_URL: ` ${url} `, CORPUS_LENS_TOKEN: `  Bearer ${TOKEN}\n` });
        expect((await c.listTools()).tools).toHaveLength(1);
        await c.close();
    });

    it("turns a rejected token into instructions a person can follow", async () => {
        await expect(bridge({ CORPUS_LENS_URL: url, CORPUS_LENS_TOKEN: "f".repeat(64) })).rejects.toThrow(
            /did not accept your access token.*Settings → Extensions/,
        );
    });

    it("says so when no token was entered, or the server cannot be reached", async () => {
        await expect(bridge({ CORPUS_LENS_URL: url, CORPUS_LENS_TOKEN: "" })).rejects.toThrow(/No access token is set/);
        await expect(bridge({ CORPUS_LENS_URL: "http://127.0.0.1:9/mcp", CORPUS_LENS_TOKEN: TOKEN })).rejects.toThrow(/Could not reach/);
    });

    it("never sends the token over plain http to a remote host", async () => {
        await expect(bridge({ CORPUS_LENS_URL: "http://example.com/corpus-lens", CORPUS_LENS_TOKEN: TOKEN })).rejects.toThrow(
            /must begin with https/,
        );
    });
});
