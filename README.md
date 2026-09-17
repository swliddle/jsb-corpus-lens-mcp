# corpus-lens-mcp

A read-only MCP server over the *Joseph the Prophet* corpus index: 2,999 source
documents segmented into 62,508 passages, each embedded with Google's
`gemini-embedding-001` (768 dims). A query is embedded the same way and ranked
locally; the answer is a chronological reading list of passages — never a claim.

This is a TypeScript consumer of the **data** in the pipeline's `corpus-lens`
bundle (`cache/` and `themes/`). It replaces the bundle's Python server; it does
not build or modify the index.

## Tools

| Tool | What it returns |
|---|---|
| `corpus_search(query, top=12, distinct=true)` | passages nearest in meaning to any wording |
| `theme_lens(theme, top=12, distinct=true)` | passages most likely to carry a named theme |
| `list_themes()` | the theme names |

Hits are `{stem, unit, rank, score, snippet, also_in}`, returned both as rendered
text and as `structuredContent`. `top` is 1–100; a query is at most 4,000 characters.

**Editions.** A fifth of the corpus is the same text in another edition (RB1, BoC,
DC1835, DC1844…), and their vectors are near-identical, so an unfiltered top 12 is
often four texts three times over. With `distinct` (the default) passages from
*different documents* whose vectors agree at ≥ `--edition-similarity` (0.95) become
one hit: the earliest edition, with the rest listed chronologically in `also_in`.
Two passages of the same document are never merged. `distinct=false` returns
every edition as its own hit, for comparing variants.

## Layout

    src/
      config.ts              env + flags → one validated Config; fails at startup, not mid-request
      errors.ts              LensError (coded): every refusal is named
      index/npy.ts           .npy reader (float32, C-order, 2-D — anything else is refused)
      index/corpusIndex.ts   load once, validate against the manifest, pre-normalize; chronology
      themes.ts              taxonomy parsed once into a catalog
      search.ts              rank(): pure, synchronous, single pass
      embedding/embedder.ts  the ONE seam to an embedding provider
      embedding/gemini.ts    Google implementation (retry on transient errors only, timeouts)
      embedding/cached.ts    in-memory LRU + in-flight de-duplication
      usage/ledger.ts        ceilings from in-memory counters, JSONL as the durable record
      lens.ts                LensService: validate → admit → embed → rank → record
      auth.ts                bearer tokens → caller names
      mcp/server.ts          tool registration
      mcp/http.ts            stateless Streamable HTTP at /mcp, GET /healthz
      main.ts                composition root
    desktop-extension/       Claude Desktop extension (manifest + stdio→HTTP bridge)

## Run

    npm install
    npm run build
    # .env (git-ignored):  GOOGLE_API_KEY=...
    npm start -- --transport http \
        --cache-dir /path/to/bundle/cache \
        --themes "/path/to/bundle/themes/Theme Descriptions.txt" \
        --usage-log /var/lib/corpus-lens/usage.jsonl \
        --verify-bundle /path/to/bundle \
        --allow-anonymous          # dev only; otherwise set CORPUS_API_TOKENS

`--transport stdio` (the default) serves Claude Code / Claude Desktop locally.

| Flag | Env | Default |
|---|---|---|
| `--transport` | `CORPUS_TRANSPORT` | `stdio` |
| `--host` / `--port` | `CORPUS_HOST` / `CORPUS_PORT` | `127.0.0.1` / `8765` |
| `--allowed-hosts` | `CORPUS_ALLOWED_HOSTS` | loopback only |
| `--cache-dir` | `CORPUS_CACHE_DIR` | required |
| `--themes` | `CORPUS_THEMES` | required |
| `--usage-log` | `CORPUS_USAGE_LOG` | required |
| `--verify-bundle` | `CORPUS_VERIFY_BUNDLE` | off |
| — | `CORPUS_API_TOKENS` | required for http: `name:token,…`; env only |
| `--allow-anonymous` | `CORPUS_ALLOW_ANONYMOUS` | `false` |
| `--caller` | `CORPUS_MCP_CALLER` | `shared` |
| `--per-caller-daily` | `CORPUS_PER_CALLER_DAILY` | `200` |
| `--dollars-daily` | `CORPUS_DOLLARS_DAILY` | `1.00` |
| `--dollars-per-m-tokens` | `CORPUS_DOLLARS_PER_M_TOKENS` | `2.00` |
| `--edition-similarity` | `CORPUS_EDITION_SIMILARITY` | `0.95` |
| — | `GOOGLE_API_KEY` or `GEMINI_API_KEY` | required; env only, never a flag |

## Deploy

Ubuntu + Apache + systemd: see [deploy/DEPLOY.md](deploy/DEPLOY.md).

## Claude Desktop extension

`desktop-extension/` is a Desktop Extension (`.mcpb`) for people who use the
Claude Desktop app: a double-click install with a field for their token (kept in
the OS keychain), no Node install and no JSON editing. Inside is a ~100-line,
dependency-free bridge from stdio to this server's HTTP endpoint; it runs on the
Node that ships with Claude Desktop.

    npm run extension:pack        # → desktop-extension/corpus-lens.mcpb (git-ignored)

Send people the `.mcpb`, `desktop-extension/INSTALL-FOR-USERS.md`, and — separately —
their token. The server address is a setting with a default, so a URL change
does not need a new file. Claude Code users don't need the extension:
`claude mcp add --transport http … --header "Authorization: Bearer <token>"`.

## Test

    npm test                                   # unit tests, no data or key needed
    CORPUS_BUNDLE_DIR=/path/to/bundle npm test # + the real index, still no key

## Updating the corpus

Stop the service, replace `cache/` and `themes/` from the new bundle, start with
`--verify-bundle`. The server refuses to start if the manifest's model or cache
form is not what it was written for, or if vectors and manifest do not line up.

## Differences from the Python server

- The index is loaded once at startup (Python re-read 200 MB per query).
- Results are ordered by date parsed from the stem (`ca-` and undated stems
  handled), then document, then reading order — not by comparing labels as text.
- Ceilings are enforced atomically from memory; days are UTC days.
- Repeat queries (notably the ten theme queries) are served from an in-memory
  cache at no cost; they still count toward the per-caller ceiling.
- The server authenticates bearer tokens itself, one per person; the caller's
  name comes from the token, never from a request header.
- `top` and query length are bounded.
- Editions of one text are merged into a single hit by default (`distinct`).
