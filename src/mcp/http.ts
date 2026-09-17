import type { AddressInfo } from "node:net";
import { createServer, type IncomingMessage, type Server, type ServerResponse } from "node:http";
import type { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import type { AuthInfo } from "@modelcontextprotocol/sdk/server/auth/types.js";
import type { TokenRegistry } from "../auth.js";

export interface HttpOptions {
    host: string;
    port: number;
    allowedHosts?: string[] | undefined;
    /** undefined = anonymous (development only; main.ts refuses this unless explicitly allowed). */
    tokens?: TokenRegistry | undefined;
    /** A fresh McpServer per request — the endpoint is stateless, so any replica can answer any call. */
    newServer: () => McpServer;
    health: () => Record<string, unknown>;
}

const MAX_BODY_BYTES = 64 * 1024; // a query is a few KB at most

/**
 * Streamable HTTP at POST /mcp, stateless (no sessions, JSON responses), plus
 * GET /healthz. Binds to loopback: TLS belongs to the reverse proxy in front;
 * the bearer token is checked HERE, before the body is read.
 */
export function startHttp(opts: HttpOptions): Promise<Server> {

    const http = createServer((req, res) => {
        handle(req, res).catch((e) => {
            console.error(`request failed: ${(e as Error).stack ?? e}`);
            if (!res.headersSent) sendJson(res, 500, rpcError(-32603, "Internal server error"));
            else res.end();
        });
    });

    async function handle(req: IncomingMessage, res: ServerResponse): Promise<void> {
        const path = (req.url ?? "/").split("?")[0];
        if (path === "/healthz" && req.method === "GET") return sendJson(res, 200, opts.health());
        if (path !== "/mcp") return sendJson(res, 404, { error: "not found" });
        if (req.method !== "POST") {
            res.setHeader("Allow", "POST");
            return sendJson(res, 405, rpcError(-32000, "Method not allowed: this endpoint is stateless, use POST"));
        }

        let auth: AuthInfo | undefined;
        if (opts.tokens) {
            const caller = opts.tokens.identify(req.headers.authorization);
            if (!caller) {
                console.error(`[corpus-lens] 401 from ${req.socket.remoteAddress} (${req.headers["x-forwarded-for"] ?? "direct"})`);
                res.setHeader("WWW-Authenticate", 'Bearer realm="corpus-lens"');
                return sendJson(res, 401, rpcError(-32001, "Unauthorized: a valid bearer token is required"));
            }
            auth = { token: "", clientId: caller, scopes: [] }; // the token itself goes no further
        }

        let body: unknown;
        try {
            body = JSON.parse(await readBody(req));
        } catch (e) {
            const tooLarge = (e as Error).message === "too large";
            return sendJson(res, tooLarge ? 413 : 400, rpcError(-32700, tooLarge ? "Request too large" : "Parse error"));
        }

        const server = opts.newServer();
        const transport = new StreamableHTTPServerTransport({
            sessionIdGenerator: undefined,
            enableJsonResponse: true,
            enableDnsRebindingProtection: true,
            allowedHosts: opts.allowedHosts ?? loopbackHosts(http),
        });
        res.on("close", () => {
            void transport.close();
            void server.close();
        });
        await server.connect(transport);
        await transport.handleRequest(Object.assign(req, { auth }), res, body);
    }

    return new Promise((resolve, reject) => {
        http.once("error", reject);
        http.listen(opts.port, opts.host, () => resolve(http));
    });
}

/** What a loopback client (or Apache's ProxyPass, which rewrites Host to the backend) sends. */
function loopbackHosts(http: Server): string[] {
    const { port } = http.address() as AddressInfo;
    return [`127.0.0.1:${port}`, `localhost:${port}`];
}

function readBody(req: IncomingMessage): Promise<string> {
    return new Promise((resolve, reject) => {
        const chunks: Buffer[] = [];
        let size = 0;
        req.on("data", (c: Buffer) => {
            size += c.length;
            if (size > MAX_BODY_BYTES) {
                reject(new Error("too large"));
                req.destroy();
                return;
            }
            chunks.push(c);
        });
        req.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
        req.on("error", reject);
    });
}

function rpcError(code: number, message: string) {
    return { jsonrpc: "2.0", error: { code, message }, id: null };
}

function sendJson(res: ServerResponse, status: number, payload: unknown): void {
    res.writeHead(status, { "Content-Type": "application/json" }).end(JSON.stringify(payload));
}
