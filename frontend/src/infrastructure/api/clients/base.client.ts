import {
    Err,
    ApiError,
    Result,
    Ok,
    type Option,
    None,
    Some,
    fromNullable,
} from "../../../shared/types";
import { z } from "zod"
import { buildValidationErrorMessage } from "../utils";
import { type RequestOptions, type Api, noRequestOptions } from "../types/types"
import type { AppConfig } from "../../config"

const DEFAULT_OPTIONS: RequestInit = {
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json",
  },
  credentials: 'include'
};


// Extract a human-readable error string out of an HTTP error body.
// FastAPI conventionally puts it under `detail.message` or `detail`;
// fall back to the raw text when the body isn't JSON or the shape
// doesn't match.
function extractErrorMessage(text: string): string {
    const parsed = Result.safe(() => JSON.parse(text) as unknown);
    if (parsed.isErr()) return text;

    const detailOpt: Option<unknown> = fromNullable(parsed.unwrap()).andThen(
        (b) =>
            typeof b === "object" && b !== null && "detail" in b
                ? fromNullable((b as { detail: unknown }).detail)
                : None,
    );

    const messageOpt: Option<string> = detailOpt.andThen((detail) => {
        if (typeof detail === "string") return Some(detail);
        if (
            typeof detail === "object" &&
            detail !== null &&
            "message" in detail &&
            typeof (detail as { message: unknown }).message === "string"
        ) {
            return Some((detail as { message: string }).message);
        }
        return None;
    });

    return messageOpt.unwrapOr(text);
}


async function fetchApi<T>(
    url: string,
    options: RequestInit,
    responseBodySchema: z.ZodType<T>,
    baseURL: string,
    timeoutMs: number,
): Promise<Result<T, ApiError>> {
    const method = options.method ?? "GET";
    const startedAt = performance.now();
    console.debug(`[api] → ${method} ${url}`, timeoutMs ? `(timeout ${timeoutMs}ms)` : "");

    try {

        const effectiveOptions: RequestInit = {
             ...DEFAULT_OPTIONS,
             ...options,
             headers: {
                 ...DEFAULT_OPTIONS.headers,
                 ...options.headers
             }
         }

        if (timeoutMs) {
            effectiveOptions.signal = options.signal
                ? AbortSignal.any([options.signal, AbortSignal.timeout(timeoutMs)])
                : AbortSignal.timeout(timeoutMs);
        }

        const fullUrl = new URL(url, baseURL).toString()
        

        const response = await fetch(fullUrl, effectiveOptions);
        const elapsedMs = Math.round(performance.now() - startedAt);

        if (!response.ok) {
            const text = await response.text()
            return Err(new ApiError(response.status, extractErrorMessage(text)))
        }

        if (response.status === 204 || response.status === 205) {
            console.warn(`[api] ✗ ${method} ${url} → ${response.status} No Content (${elapsedMs}ms)`);
            return Err(new ApiError(response.status, "No content"))
        }

        // Header.get() returns null when absent — model that absence
        // explicitly via Option rather than silently coalescing to "".
        const contentTypeOpt = fromNullable(response.headers.get("Content-Type"));
        const isJson = contentTypeOpt
            .map((ct) => ct.includes("application/json"))
            .unwrapOr(false);

        if (isJson) {

            const data: unknown = await response.json()

            const parsed = responseBodySchema.safeParse(data)

            if (!parsed.success) {
                const validationError = buildValidationErrorMessage(parsed.error)
                console.error(
                    `[api] ✗ ${method} ${url} → schema validation failed (${elapsedMs}ms)`,
                    { issues: parsed.error.issues, received: data },
                );
                return Err(new ApiError(422, validationError))
            }

            console.debug(`[api] ✓ ${method} ${url} → ${response.status} (${elapsedMs}ms)`);
            return Ok(parsed.data)
        } else {
            const ctDisplay = contentTypeOpt.unwrapOr("no content-type");
            console.warn(
                `[api] ✗ ${method} ${url} → unexpected content-type "${ctDisplay}" (${elapsedMs}ms)`,
            );
            return Err(new ApiError(response.status, `Expected JSON, got: ${ctDisplay}`));
        }

    } catch (error) {

        const elapsedMs = Math.round(performance.now() - startedAt);

        if (error instanceof DOMException && error.name === "TimeoutError") {
            console.warn(`[api] ✗ ${method} ${url} → timed out after ${elapsedMs}ms`);
            return Err(new ApiError(408, "Request timed out"));
        }
        if (error instanceof DOMException && error.name === "AbortError") {
            console.debug(`[api] ⊘ ${method} ${url} → cancelled (${elapsedMs}ms)`);
            return Err(new ApiError(0, "Request was cancelled"));
        }
        if (error instanceof TypeError) {
            console.error(`[api] ✗ ${method} ${url} → network error (${elapsedMs}ms)`, error);
            return Err(new ApiError(0, "Network error"));
        }
        // Anything else is a programmer error — let it throw
        console.error(`[api] ✗ ${method} ${url} → unexpected error (${elapsedMs}ms)`, error);
        throw error;
    }
}


export class ApiClient implements Api {
    private readonly baseURL: string
    private readonly defaultTimeoutMs: number

    constructor(config: AppConfig) {
        this.baseURL = config.api.baseURL
        this.defaultTimeoutMs = config.api.defaultTimeoutMs
    }

    getJson<T>(
        url: string,
        schema: z.ZodType<T>,
        options: RequestOptions = noRequestOptions
    ) {
        return fetchApi(
            url,
            {
                method: "GET",
                signal: options.signal.into(null),
                headers: options.headers.into(),
            },
            schema,
            this.baseURL,
            options.timeoutMs.unwrapOr(this.defaultTimeoutMs)
        )
    }

    postJson<T, B=unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = noRequestOptions
    ) {
        console.log(this.baseURL)
        return fetchApi(
            url,
            {
                method: "POST",
                signal: options.signal.into(null),
                headers: options.headers.into(),
                body: JSON.stringify(body)
            },
            schema,
            this.baseURL,
            options.timeoutMs.unwrapOr(this.defaultTimeoutMs)
        )
    }


    putJson<T, B=unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = noRequestOptions
    ) {
        return fetchApi(
            url,
            {
                method: "PUT",
                signal: options.signal.into(null),
                headers: options.headers.into(),
                body: JSON.stringify(body)
            },
            schema,
            this.baseURL,
            options.timeoutMs.unwrapOr(this.defaultTimeoutMs)
        )
    }

    deleteJson<T>(
        url: string,
        schema: z.ZodType<T>,
        options: RequestOptions = noRequestOptions
    ) {
        return fetchApi(
            url,
            {
                method: "DELETE",
                signal: options.signal.into(null),
                headers: options.headers.into(),
            },
            schema,
            this.baseURL,
            options.timeoutMs.unwrapOr(this.defaultTimeoutMs)
        )
    }

    patchJson<T, B = unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = noRequestOptions
     ) {
        return fetchApi(
            url,
            {
                method: "PATCH",
                signal: options.signal.into(null),
                headers: options.headers.into(),
                body: JSON.stringify(body)
            },
            schema,
            this.baseURL,
            options.timeoutMs.unwrapOr(this.defaultTimeoutMs)
        )
    }
}
