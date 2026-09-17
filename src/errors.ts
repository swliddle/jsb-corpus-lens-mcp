/**
 * Every refusal the lens makes is a LensError: named, loud, never a partial
 * answer. `code` lets transports and tests branch without parsing messages.
 */
export type LensErrorCode =
    | "INDEX_INVALID"
    | "THEMES_INVALID"
    | "UNKNOWN_THEME"
    | "BAD_QUERY"
    | "CEILING_CALLER"
    | "CEILING_GLOBAL"
    | "EMBEDDING_FAILED"
    | "CONFIG_INVALID";

export class LensError extends Error {
    readonly code: LensErrorCode;

    constructor(code: LensErrorCode, message: string, options?: ErrorOptions) {
        super(message, options);
        this.name = "LensError";
        this.code = code;
    }
}
