import type { z } from "zod";
import { fromNullable, None, type Option, type Result } from "../../../shared/types";
import type { ApiError } from "../../../shared/types";

export interface RequestOptions {
    signal: Option<AbortSignal>;
    timeoutMs: Option<number>;
    headers: Option<HeadersInit>;
}

/**
 * Empty `RequestOptions` — every field `None`. Use as the default when no
 * caller-supplied options exist.
 */
export const noRequestOptions: RequestOptions = {
    signal: None,
    timeoutMs: None,
    headers: None,
};

/**
 * Build a `RequestOptions` from raw nullable fields. This is the bridge
 * between the React-Query world (where `signal: AbortSignal | undefined`
 * is handed to us by `queryFn`) and the Option-typed API surface. Each
 * field is wrapped via `fromNullable`.
 */
export function requestOptions(
    raw: {
        signal?: AbortSignal | null;
        timeoutMs?: number | null;
        headers?: HeadersInit | null;
    } = {},
): RequestOptions {
    return {
        signal: fromNullable(raw.signal),
        timeoutMs: fromNullable(raw.timeoutMs),
        headers: fromNullable(raw.headers),
    };
}

export interface Api {
    getJson<TResponse>(
        url: string,
        responseSchema: z.ZodType<TResponse>,
        options?: RequestOptions,
    ): Promise<Result<TResponse, ApiError>>;

    postJson<TResponse, TBody = unknown>(
        url: string,
        body: TBody,
        responseSchema: z.ZodType<TResponse>,
        options?: RequestOptions,
    ): Promise<Result<TResponse, ApiError>>;

    putJson<TResponse, TBody = unknown>(
        url: string,
        body: TBody,
        responseSchema: z.ZodType<TResponse>,
        options?: RequestOptions,
    ): Promise<Result<TResponse, ApiError>>;

    deleteJson<TResponse>(
        url: string,
        responseSchema: z.ZodType<TResponse>,
        options?: RequestOptions,
    ): Promise<Result<TResponse, ApiError>>;

    patchJson<TResponse, TBody = unknown>(
        url: string,
        body: TBody,
        responseSchema: z.ZodType<TResponse>,
        options?: RequestOptions,
    ): Promise<Result<TResponse, ApiError>>;
}