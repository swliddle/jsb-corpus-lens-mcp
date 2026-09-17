import { appendFile, mkdir, readFile } from "node:fs/promises";
import { dirname } from "node:path";
import { LensError } from "../errors.js";

export interface Ceilings {
    perCallerDaily: number;
    dollarsDaily: number;
}

export interface UsageRow {
    caller: string;
    tool: string;
    status: "ok" | `error:${string}`;
    input_tokens: number;
    cost: number;
    cached: boolean;
    elapsed_s: number;
}

/**
 * Who asked, and what it cost. The JSONL file is the durable record (and the
 * server's ONE write); the ceilings are enforced from in-memory counters that
 * are hydrated from that file at startup, so a restart never resets a day.
 *
 * `admit` is synchronous — check and count happen in one turn of the event
 * loop, so concurrent requests cannot slip past a ceiling together. Days are
 * UTC days.
 */
export class UsageLedger {
    private day = "";
    private queries = new Map<string, number>();
    private dollars = 0;
    private writes: Promise<void> = Promise.resolve();

    private constructor(
        private readonly path: string,
        private readonly model: string,
        private readonly ceilings: Ceilings,
        private readonly now: () => Date,
    ) {}

    static async open(path: string, model: string, ceilings: Ceilings, now: () => Date = () => new Date()): Promise<UsageLedger> {
        const ledger = new UsageLedger(path, model, ceilings, now);
        await mkdir(dirname(path), { recursive: true });
        ledger.rollover();
        let text = "";
        try {
            text = await readFile(path, "utf8");
        } catch {
            return ledger; // no log yet
        }
        for (const line of text.split("\n")) {
            if (!line.trim()) continue;
            try {
                const r = JSON.parse(line) as Partial<UsageRow> & { ts?: string };
                if (r.status !== "ok" || String(r.ts ?? "").slice(0, 10) !== ledger.day) continue;
                ledger.count(r.caller ?? "shared", Number(r.cost) || 0);
            } catch {
                // a torn line is not worth refusing service over
            }
        }
        return ledger;
    }

    /** Refuses BY NAME when a ceiling is reached; otherwise counts the query against the caller. */
    admit(caller: string): void {
        this.rollover();
        const { perCallerDaily, dollarsDaily } = this.ceilings;
        if (this.dollars >= dollarsDaily) {
            throw new LensError(
                "CEILING_GLOBAL",
                `the lens's global daily ceiling of $${dollarsDaily.toFixed(2)} is reached ` +
                    `($${this.dollars.toFixed(4)} spent today, UTC) — no query runs until tomorrow; nothing was retrieved`,
            );
        }
        const n = this.queries.get(caller) ?? 0;
        if (n >= perCallerDaily) {
            throw new LensError(
                "CEILING_CALLER",
                `${caller} has reached the per-caller daily ceiling of ${perCallerDaily} queries — nothing was retrieved`,
            );
        }
        this.queries.set(caller, n + 1);
    }

    /** Settles an admitted query: a failure gives the caller their query back; a success adds its cost. */
    record(row: UsageRow): void {
        this.rollover();
        if (row.status === "ok") this.dollars += row.cost;
        else this.queries.set(row.caller, Math.max(0, (this.queries.get(row.caller) ?? 1) - 1));

        const line = JSON.stringify({ ts: this.now().toISOString(), stage: "corpus_mcp", model: this.model, ...row }) + "\n";
        this.writes = this.writes
            .then(() => appendFile(this.path, line, "utf8"))
            .catch((e) => console.error(`usage log write failed: ${(e as Error).message}`));
    }

    usage(caller: string): { queries: number; dollars: number } {
        this.rollover();
        return { queries: this.queries.get(caller) ?? 0, dollars: this.dollars };
    }

    /** Resolves when every row recorded so far is on disk. */
    flush(): Promise<void> {
        return this.writes;
    }

    private count(caller: string, cost: number): void {
        this.queries.set(caller, (this.queries.get(caller) ?? 0) + 1);
        this.dollars += cost;
    }

    private rollover(): void {
        const today = this.now().toISOString().slice(0, 10);
        if (today === this.day) return;
        this.day = today;
        this.queries = new Map();
        this.dollars = 0;
    }
}
