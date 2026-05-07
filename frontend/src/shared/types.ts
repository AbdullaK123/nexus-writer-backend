// ─── Option<T> ───────────────────────────────────────────────

export type Some<T> = { readonly _tag: "Some"; readonly value: T };
export type None = { readonly _tag: "None" };
export type Option<T> = Some<T> | None;

export const Some = <T>(value: T): Some<T> => ({ _tag: "Some", value });
export const None: None = { _tag: "None" };

export function isSome<T>(option: Option<T>): option is Some<T> {
    return option._tag === "Some";
}

export function isNone<T>(option: Option<T>): option is None {
    return option._tag === "None";
}

// ─── Result<T, E> ────────────────────────────────────────────

export type Ok<T> = { readonly _tag: "Ok"; readonly value: T };
export type Err<E> = { readonly _tag: "Err"; readonly error: E };
export type Result<T, E> = Ok<T> | Err<E>;

export const Ok = <T>(value: T): Ok<T> => ({ _tag: "Ok", value });
export const Err = <E>(error: E): Err<E> => ({ _tag: "Err", error });

export function isOk<T, E>(result: Result<T, E>): result is Ok<T> {
    return result._tag === "Ok";
}

export function isErr<T, E>(result: Result<T, E>): result is Err<E> {
    return result._tag === "Err";
}

// ─── Transformers ────────────────────────────────────────────

export function mapResult<T, U, E>(result: Result<T, E>, fn: (value: T) => U): Result<U, E> {
    return result._tag === "Ok" ? Ok(fn(result.value)) : result;
}

export function mapOption<T, U>(option: Option<T>, fn: (value: T) => U): Option<U> {
    return option._tag === "Some" ? Some(fn(option.value)) : None;
}

export function fromNullable<T>(value: T | null | undefined): Option<T> {
    return value != null ? Some(value) : None;
}

// ─── Unwrap (bridges to React Query — throws on Err/None) ───

export function unwrapResult<T>(result: Result<T, unknown>): T {
    if (result._tag === "Ok") return result.value;
    throw result.error;
}

export function unwrapOption<T>(option: Option<T>, message?: string): T {
    if (option._tag === "Some") return option.value;
    throw new Error(message ?? "Unwrapped a None value");
}

// ─── ApiError ────────────────────────────────────────────────

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

// ─── Exhaustive Switch Helper ────────────────────────────────

export function assertNever(x: never): never {
    throw new Error(`Unhandled case: ${x}`);
}

// ─── Utility Types ───────────────────────────────────────────

export type Callback = () => void;