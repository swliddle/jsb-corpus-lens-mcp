# Deploying corpus-lens-mcp (Ubuntu, Apache, systemd)

Same shape as nauvoo-mcp: Apache terminates TLS and proxies a path to a Node
process on loopback; the Node process checks the bearer token.

    client ──HTTPS──▶ Apache :443 /corpus-lens ──HTTP──▶ 127.0.0.1:8765/mcp
                                                          │
                                       Google embedding API ◀┘ (one call per uncached query)

## One-time setup

    node -v                                   # must be 22 or newer
    sudo useradd --system --home /nonexistent --shell /usr/sbin/nologin corpus-lens

    # code (read-only to the service)
    sudo mkdir -p /var/www/corpus-lens-mcp
    # on the build machine:  npm ci && npm run build
    # then copy ALL THREE of  package.json  package-lock.json  dist/  to the server
    # (npm ci installs nothing without the lockfile) and:
    cd /var/www/corpus-lens-mcp && sudo npm ci --omit=dev
    sudo chown -R root:root /var/www/corpus-lens-mcp
    sudo chmod -R a+rX /var/www/corpus-lens-mcp      # root's umask may have made node_modules private
    sudo -u corpus-lens test -r node_modules/@modelcontextprotocol/sdk/package.json && echo "code readable"

    # data — StateDirectory creates /var/lib/corpus-lens on first start; make it now to load the bundle
    sudo install -d -o corpus-lens -g corpus-lens -m 750 /var/lib/corpus-lens
    sudo unzip corpus-lens-bundle-*.zip -d /var/lib/corpus-lens/bundle     # needs cache/ themes/ MANIFEST.json
    # AFTER unzipping — the bundle's files are mode 600 and unzip keeps that, so as
    # extracted they are readable by root alone:
    sudo chown -R corpus-lens:corpus-lens /var/lib/corpus-lens
    sudo chmod -R u+rX /var/lib/corpus-lens
    sudo -u corpus-lens test -r /var/lib/corpus-lens/bundle/MANIFEST.json && echo "bundle readable"

    # secrets
    sudo install -d -m 700 /etc/corpus-lens
    sudo install -m 600 /dev/null /etc/corpus-lens/env
    sudoedit /etc/corpus-lens/env

`/etc/corpus-lens/env`:

    GOOGLE_API_KEY=<a key made for THIS server, restricted to the Generative Language API>
    CORPUS_API_TOKENS=steve:<token>,eric:<token>

One token per person: `openssl rand -hex 32`. The name before the colon is what
appears in the usage log and what the per-caller daily ceiling counts.

    sudo cp deploy/corpus-lens-mcp.service /etc/systemd/system/
    sudo systemctl daemon-reload && sudo systemctl enable --now corpus-lens-mcp
    journalctl -u corpus-lens-mcp -n 20
    #   bundle manifest verified
    #   index loaded in … ms: 2999 files, 62508 passages, 768 dims, 10 themes
    #   serving on http://127.0.0.1:8765/mcp — bearer tokens for: steve, eric

Add `deploy/apache-corpus-lens.conf` to the TLS vhost, then:

    sudo apachectl configtest && sudo systemctl reload apache2

## Check it

    curl -s http://127.0.0.1:8765/healthz                          # on the server; not exposed by Apache
    curl -s -o /dev/null -w '%{http_code}\n' -X POST https://<host>/corpus-lens     # 401 — no token
    curl -s -X POST https://<host>/corpus-lens \
      -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
      -H 'Accept: application/json, text/event-stream' \
      -d '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"list_themes","arguments":{}}}'

## Connect a client

    claude mcp add --transport http corpus-lens https://<host>/corpus-lens \
        --header "Authorization: Bearer <token>"

## Routine operations

| Task | How |
|---|---|
| Add / revoke a person | edit `CORPUS_API_TOKENS` in `/etc/corpus-lens/env`, `sudo systemctl restart corpus-lens-mcp` |
| New corpus bundle | stop the service, replace `/var/lib/corpus-lens/bundle`, `chown -R corpus-lens:` + `chmod -R u+rX` it, start — startup verifies MANIFEST.json and refuses a mismatch |
| New code | copy `dist/` + lockfile, `npm ci --omit=dev`, restart |
| Who asked what | `/var/lib/corpus-lens/usage.jsonl` — one JSON line per query (caller, tool, tokens, cost, cached) |
| Failed logins | `journalctl -u corpus-lens-mcp | grep 401` |

Keep `usage.jsonl` across deploys: the daily ceilings are restored from it at startup.
