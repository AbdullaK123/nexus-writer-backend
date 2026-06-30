// ─── Option / Result ────────────────────────────────────────
//
// Re-exported from `oxide.ts` — Rust's Option<T> / Result<T, E> for
// TypeScript with full method chaining. Do NOT hand-roll combinators
// here; everything lives on the values themselves:
//
//     opt.isSome() / opt.isNone()
//     opt.unwrap() / opt.unwrapOr(default) / opt.unwrapOrElse(fn)
//     opt.expect("msg")
//     opt.map(fn) / opt.andThen(fn) / opt.mapOr(default, fn)
//     opt.into(null)            // → T | null
//
//     res.isOk() / res.isErr()
//     res.unwrap() / res.unwrapErr()
//     res.unwrapOr(default) / res.unwrapOrElse(fn)
//     res.map(fn) / res.mapErr(fn) / res.andThen(fn)
//     res.ok()                  // → Option<T>
//
//     match(value, { Some: ..., None: ... })
//     match(value, { Ok: ...,   Err: ...  })
//
//     Option.nonNull(x)         // null/undefined/NaN → None, else Some
//     Result.safe(fn)           // capture throws as Err<Error>
//     Result.safe(promise)      // capture rejections as Err<Error>
//     Result.all(...) / Option.all(...)
//
// See https://github.com/traverse1984/oxide.ts for the full surface.

export {
    Option,
    Some,
    None,
    Result,
    Ok,
    Err,
    match,
    Fn,
    _,
} from "oxide.ts";

import { Some, None, type Option, type Result } from "oxide.ts";

// ─── Compat shims ───────────────────────────────────────────
// Thin named adapters for the two cross-boundary cases where a verb
// reads more honestly than the underlying call. Keep this list small —
// every alias is debt.

/**
 * Wrap a possibly-nullish value into an `Option`. The boundary helper
 * for code that interfaces with native `T | null | undefined` APIs
 * (DOM, JSON, third-party, React Query). Note: this preserves the
 * inner type literally; unlike `Option.nonNull`, it does not strip
 * `NaN` from a `number` input.
 */
export function fromNullable<T>(value: T | null | undefined): Option<T> {
    return value == null ? None : Some(value);
}

/**
 * React Query bridge. Awaits a `Promise<Result<T, E>>` and unwraps —
 * `Ok` resolves to `T`, `Err` throws. Use ONLY in `queryFn` /
 * `mutationFn`; everywhere else, prefer `match` / `unwrapOr` /
 * `andThen`.
 */
export async function unwrapResultAsync<T, E>(
    promise: Promise<Result<T, E>>,
): Promise<T> {
    const result = await promise
    if (result.isErr()) 
        throw result.unwrapErr()
    return result.unwrap()
}

// ─── ApiError ────────────────────────────────────────────────
// Domain error type carried in `Result<T, ApiError>` from the API
// client layer. Lives here so any layer can match on it without
// importing from the infrastructure tree.

export class ApiError extends Error {
    public readonly name = "ApiError" as const;
    public readonly status: number;
    public readonly detail: string;

    constructor(status: number, detail: string) {
        super(detail);
        this.status = status;
        this.detail = detail;
    }
}

// ─── Misc utility types ──────────────────────────────────────

export type Callback = () => void;

/**
 * Exhaustiveness helper for switch/match on tagged unions. The compile
 * error you get when forgetting a case is the whole point.
 */
export function assertNever(x: never): never {
    throw new Error(`Unreachable: unexpected value ${JSON.stringify(x)}`);
}
