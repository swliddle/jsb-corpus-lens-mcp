#!/usr/bin/env node
/**
 * corpus-lens desktop bridge: MCP over stdio on this side, the corpus-lens
 * server's stateless Streamable HTTP endpoint on the other, with the user's
 * bearer token attached. No dependencies — it runs on the Node that ships
 * inside Claude Desktop.
 *
 * stdout carries protocol messages ONLY; anything for a human goes to stderr
 * (Claude Desktop keeps it in the extension's log). The token is never logged.
 */
"use strict";

const readline = require("node:readline");

const TIMEOUT_MS = 30_000;

const url = (process.env.CORPUS_LENS_URL || "").trim();
// People paste tokens with stray whitespace, or with the "Bearer " they were told about.
const token = (process.env.CORPUS_LENS_TOKEN || "").trim().replace(/^Bearer\s+/i, "");

const log = (msg) => process.stderr.write(`[corpus-lens] ${msg}\n`);
const send = (msg) => process.stdout.write(JSON.stringify(msg) + "\n");

function configProblem() {
    if (!token) return "No access token is set. Open Settings → Extensions → Joseph Smith Corpus Lens and enter the token you were sent.";
    let u;
    try {
        u = new URL(url);
    } catch {
        return `The server address "${url}" is not a valid URL. Open Settings → Extensions → Joseph Smith Corpus Lens to correct it.`;
    }
    const loopback = u.hostname === "localhost" || u.hostname === "127.0.0.1";
    if (u.protocol !== "https:" && !loopback) return "The server address must begin with https:// — the access token is never sent over an unencrypted connection.";
    return null;
}

function explain(status) {
    if (status === 401) return "The corpus-lens server did not accept your access token. Open Settings → Extensions → Joseph Smith Corpus Lens, re-enter the token exactly as it was sent to you, and try again. If it still fails, ask the administrator for a new token.";
    if (status === 404 || status === 503 || status === 502) return `The corpus-lens server is not available right now (HTTP ${status}). Try again in a few minutes; if it persists, tell the administrator.`;
    return `The corpus-lens server answered with an unexpected status (HTTP ${status}).`;
}

/** Every request in `message` (one message or a batch) gets a JSON-RPC error; notifications get nothing. */
function fail(message, text) {
    log(text);
    for (const m of Array.isArray(message) ? message : [message]) {
        if (m && m.id !== undefined && m.id !== null && m.method) send({ jsonrpc: "2.0", id: m.id, error: { code: -32000, message: text } });
    }
}

function fromSse(text) {
    return text
        .split(/\r?\n\r?\n/)
        .map((event) => event.split(/\r?\n/).filter((l) => l.startsWith("data:")).map((l) => l.slice(5).trimStart()).join("\n"))
        .filter(Boolean)
        .map((data) => JSON.parse(data));
}

async function forward(message) {
    const problem = configProblem();
    if (problem) return fail(message, problem);

    let res;
    try {
        res = await fetch(url, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                Accept: "application/json, text/event-stream",
                Authorization: `Bearer ${token}`,
            },
            body: JSON.stringify(message),
            signal: AbortSignal.timeout(TIMEOUT_MS),
        });
    } catch (e) {
        const why = e && e.name === "TimeoutError" ? "it did not answer in time" : (e && e.cause && e.cause.code) || (e && e.message) || "unknown error";
        return fail(message, `Could not reach the corpus-lens server (${why}). Check your internet connection and try again.`);
    }

    if (res.status === 202 || res.status === 204) return; // a notification, accepted
    const body = await res.text();
    if (!res.ok) {
        // The server's own JSON-RPC errors carry id:null; say something a person can act on instead.
        return fail(message, explain(res.status));
    }
    try {
        const replies = (res.headers.get("content-type") || "").includes("text/event-stream") ? fromSse(body) : [JSON.parse(body)];
        for (const r of replies) send(r);
    } catch {
        fail(message, "The corpus-lens server sent a reply that could not be read.");
    }
}

let inFlight = 0;
let closed = false;
const maybeExit = () => closed && inFlight === 0 && process.exit(0);

readline.createInterface({ input: process.stdin, crlfDelay: Infinity })
    .on("line", (line) => {
        if (!line.trim()) return;
        let message;
        try {
            message = JSON.parse(line);
        } catch {
            return send({ jsonrpc: "2.0", id: null, error: { code: -32700, message: "Parse error" } });
        }
        inFlight++;
        forward(message)
            .catch((e) => fail(message, `Unexpected bridge error: ${e && e.message}`))
            .finally(() => {
                inFlight--;
                maybeExit();
            });
    })
    .on("close", () => {
        closed = true;
        maybeExit();
    });

log(`bridge started → ${url || "(no server address)"}${token ? "" : " — NO TOKEN SET"}`);
