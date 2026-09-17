import { readFile } from "node:fs/promises";
import { endianness } from "node:os";
import { LensError } from "../errors.js";

export interface Matrix {
    readonly rows: number;
    readonly cols: number;
    /** Row-major, rows * cols values. */
    readonly data: Float32Array;
}

const MAGIC = Buffer.from([0x93, 0x4e, 0x55, 0x4d, 0x50, 0x59]); // \x93NUMPY

/**
 * Reads a 2-D little-endian float32, C-order .npy file (format 1.x–3.x).
 * Anything else is refused — the pipeline writes exactly this shape.
 */
export async function readNpyFloat32Matrix(path: string): Promise<Matrix> {
    const buf = await readFile(path);
    const bad = (why: string) => new LensError("INDEX_INVALID", `${path}: ${why}`);

    if (buf.length < 12 || !buf.subarray(0, 6).equals(MAGIC)) throw bad("not a .npy file");
    const major = buf[6]!;
    const headerLen = major === 1 ? buf.readUInt16LE(8) : buf.readUInt32LE(8);
    const headerStart = major === 1 ? 10 : 12;
    const dataStart = headerStart + headerLen;
    const header = buf.subarray(headerStart, dataStart).toString("latin1");

    const descr = /'descr':\s*'([^']+)'/.exec(header)?.[1];
    const fortran = /'fortran_order':\s*(True|False)/.exec(header)?.[1];
    const shape = /'shape':\s*\(\s*(\d+)\s*,\s*(\d+)\s*,?\s*\)/.exec(header);
    if (descr !== "<f4") throw bad(`expected dtype <f4, found ${descr ?? "none"}`);
    if (fortran !== "False") throw bad("expected C-order (fortran_order False)");
    if (!shape) throw bad(`expected a 2-D shape, header was ${header.trim()}`);
    if (endianness() !== "LE") throw bad("this reader requires a little-endian host");

    const rows = Number(shape[1]);
    const cols = Number(shape[2]);
    const bytes = rows * cols * 4;
    if (buf.length - dataStart !== bytes) {
        throw bad(`shape ${rows}x${cols} needs ${bytes} data bytes, file has ${buf.length - dataStart}`);
    }

    const offset = buf.byteOffset + dataStart;
    const data =
        offset % 4 === 0
            ? new Float32Array(buf.buffer, offset, rows * cols) // zero-copy view
            : new Float32Array(buf.buffer.slice(offset, offset + bytes));
    return { rows, cols, data };
}
