import type { z } from "zod";
import type { Result } from "../../../shared/types";
import type { ApiError } from "../../../shared/types";

export interface RequestOptions {
    signal?: AbortSignal;
    timeoutMs?: number;
    headers?: HeadersInit;
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