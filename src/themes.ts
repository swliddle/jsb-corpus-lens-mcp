import { readFile } from "node:fs/promises";
import { LensError } from "./errors.js";

export interface Theme {
    readonly number: number;
    readonly name: string;
    readonly description: string;
    readonly definition: string;
    readonly owns: string;
    /** What theme_lens embeds: the Definition (or, absent one, the description) plus the Owns line. */
    readonly query: string;
}

const HEADER = /^\s*(\d+)\.\s+(.+?)\s+—\s+(.*)$/;
const NUMBERED = /^\s*\d+\.\s/;

export function parseThemes(text: string): Theme[] {
    const lines = text.split(/\r?\n/);
    const starts = lines.flatMap((ln, i) => (NUMBERED.test(ln) ? [i] : []));
    const themes: Theme[] = [];

    starts.forEach((start, k) => {
        const m = HEADER.exec(lines[start]!.trimEnd());
        if (!m) return;
        const end = starts[k + 1] ?? lines.length;
        let definition = "";
        let owns = "";
        for (const ln of lines.slice(start + 1, end)) {
            const s = ln.trim();
            if (/^definition:/i.test(s)) definition = afterColon(s);
            else if (/^-?\s*Owns:/i.test(s)) owns = afterColon(s);
        }
        const description = m[3]!.trim();
        themes.push({
            number: Number(m[1]),
            name: m[2]!.trim(),
            description,
            definition,
            owns,
            query: [definition || description, owns].filter(Boolean).join(" "),
        });
    });
    return themes;
}

function afterColon(s: string): string {
    return s.slice(s.indexOf(":") + 1).trim();
}

export class ThemeCatalog {
    private readonly byKey: Map<string, Theme>;

    constructor(readonly themes: readonly Theme[]) {
        this.byKey = new Map(themes.map((t) => [key(t.name), t]));
    }

    static async load(path: string): Promise<ThemeCatalog> {
        let text: string;
        try {
            text = await readFile(path, "utf8");
        } catch (e) {
            throw new LensError("THEMES_INVALID", `cannot read the theme taxonomy at ${path} (${(e as Error).message})`);
        }
        const themes = parseThemes(text);
        if (themes.length === 0) throw new LensError("THEMES_INVALID", `no themes found in ${path}`);
        return new ThemeCatalog(themes);
    }

    names(): string[] {
        return this.themes.map((t) => t.name);
    }

    /** Case- and whitespace-insensitive; an unknown theme fails BY NAME, never a guess. */
    get(name: string): Theme {
        const t = this.byKey.get(key(name));
        if (!t) {
            throw new LensError(
                "UNKNOWN_THEME",
                `'${name}' is not a theme in the taxonomy. Known themes: ${this.names().join(", ")}.`,
            );
        }
        return t;
    }
}

function key(name: string): string {
    return name.trim().replace(/\s+/g, " ").toLowerCase();
}
