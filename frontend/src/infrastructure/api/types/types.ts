import type { z } from "zod";
import { fromNullable } from "../../../shared/types";
import type { ApiError } from "../../../shared/types";
import { type Ok, type Some, None, type Option, type Result } from "oxide.ts";

export interface RequestOptions {
    signal: Option<AbortSignal>;
    timeoutMs: Option<number>;
    headers: Option<HeadersInit>;
}

export const noRequestOptions: RequestOptions = {
    signal: None,
    timeoutMs: None,
    headers: None,
};

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

export type AsyncState<T, _E> = 
    | { status: "idle"; data: Option<never> } 
    | { status: "loading"; data: Option<never> }
    | { status: "empty"; data: Some<Ok<[]>> }
    | { status: "success"; data: Some<Ok<T>> };
