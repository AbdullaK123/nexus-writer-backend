import { Err, ApiError, type Result, Ok } from "../../../shared/types";
import { z } from "zod"
import { buildValidationErrorMessage } from "../utils";
import { type RequestOptions, type Api } from "../types/types"
import { config } from "../../config"

const DEFAULT_OPTIONS: RequestInit = {
  headers: {
    "Accept": "application/json",
    "Content-Type": "application/json",
  },
  credentials: "same-origin"
};



async function fetchApi<T>(
    url: string, 
    options: RequestInit,
    responseBodySchema: z.ZodType<T>,
    timeoutMs: number = config.api.defaultTimeoutMs
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

        const fullUrl = `${config.api.baseURL}/${url}`

        const response = await fetch(fullUrl, effectiveOptions);
        const elapsedMs = Math.round(performance.now() - startedAt);

        if (!response.ok) {
            const responseStatus = response.status
            const responseText = await response.text()
            console.warn(`[api] ✗ ${method} ${url} → ${responseStatus} (${elapsedMs}ms)`, responseText);
            return Err(new ApiError(responseStatus, responseText))
        }

        if (response.status === 204 || response.status === 205) {
            console.warn(`[api] ✗ ${method} ${url} → ${response.status} No Content (${elapsedMs}ms)`);
            return Err(new ApiError(response.status, "No content"))
        }

        const contentType = response.headers.get("Content-Type") ?? ""
        
        if (contentType.includes("application/json")) {

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
            console.warn(
                `[api] ✗ ${method} ${url} → unexpected content-type "${contentType || "none"}" (${elapsedMs}ms)`,
            );
            return Err(new ApiError(response.status, `Expected JSON, got: ${contentType || "no content-type"}`));
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

    getJson<T>(
        url: string,
        schema: z.ZodType<T>,
        options: RequestOptions = {}
    ) {
        return fetchApi(
            url, 
            { 
                method: "GET", 
                signal: options.signal, 
                headers: options.headers 
            },
            schema,
            options.timeoutMs
        )
    }
    
    postJson<T, B=unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = {}
    ) {
        return fetchApi(
            url,
            {
                method: "POST",
                signal: options.signal,
                headers: options.headers,
                body: JSON.stringify(body)
            },
            schema,
            options.timeoutMs
        )
    }


    putJson<T, B=unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = {}
    ) {
        return fetchApi(
            url,
            {
                method: "PUT",
                signal: options.signal,
                headers: options.headers,
                body: JSON.stringify(body)
            },
            schema,
            options.timeoutMs
        )
    }

    deleteJson<T>(
        url: string,
        schema: z.ZodType<T>,
        options: RequestOptions = {}
    ) {
        return fetchApi(
            url, 
            { 
                method: "DELETE", 
                signal: options.signal, 
                headers: options.headers 
            },
            schema,
            options.timeoutMs
        )
    }

    patchJson<T, B = unknown>(
        url: string,
        body: B,
        schema: z.ZodType<T>,
        options: RequestOptions = {}
     ) {
        return fetchApi(
            url,
            {
                method: "PATCH",
                signal: options.signal,
                headers: options.headers,
                body: JSON.stringify(body)
            },
            schema,
            options.timeoutMs
        )
    }
}
