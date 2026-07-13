import { createParser, type EventSourceMessage } from "eventsource-parser"
import {
    Err,
    None,
    Ok,
    Result,
    Some,
    fromNullable,
    type Callback,
    type Option,
} from "../../shared/types"
import { loadConfig } from "../config"

// ─── Error model ─────────────────────────────────────────────
// Tagged union so callers can `match` / `switch` exhaustively
// instead of regex-sniffing an Error.message.

const config = loadConfig().unwrap()

export type SseError =
    | { readonly _tag: "SseHttpError"; readonly status: number; readonly body: string }
    | { readonly _tag: "SseNoBodyError" }
    | { readonly _tag: "SseAbortedError" }
    | { readonly _tag: "SseNetworkError"; readonly cause: Error }
    | { readonly _tag: "SseStreamError"; readonly cause: Error }

const SseHttpError = (status: number, body: string): SseError => ({
    _tag: "SseHttpError",
    status,
    body,
})
const SseNoBodyError: SseError = { _tag: "SseNoBodyError" }
const SseAbortedError: SseError = { _tag: "SseAbortedError" }
const SseNetworkError = (cause: Error): SseError => ({
    _tag: "SseNetworkError",
    cause,
})
const SseStreamError = (cause: Error): SseError => ({
    _tag: "SseStreamError",
    cause,
})

// ─── Public types ────────────────────────────────────────────

export interface SseHandlers {
    onEvent: (event: EventSourceMessage) => void
    /** Optional close hook. Wrap in `Some(...)` or pass `None`. */
    onClose: Option<Callback>
}

export interface SseRequest {
    url: string
    method: Option<"GET" | "POST">
    body: Option<unknown>
    headers: Option<HeadersInit>
    signal: Option<AbortSignal>
}

// ─── Implementation ──────────────────────────────────────────

export async function streamSse(
    request: SseRequest,
    handlers: SseHandlers,
): Promise<Result<void, SseError>> {
    const method = request.method.unwrapOr("POST" as const)
    const extraHeaders: HeadersInit = request.headers.unwrapOr({})
    const body = request.body.map((v) => JSON.stringify(v)).into(null)
    const signal = request.signal.into(null)

    const fetchResult = await Result.safe(
        fetch(`${config.api.baseURL}${request.url}`, {
            method,
            headers: {
                Accept: "text/event-stream",
                "Content-Type": "application/json",
                ...extraHeaders,
            },
            body,
            credentials: "include",
            signal,
        }),
    )

    if (fetchResult.isErr()) {
        if (signal?.aborted) return Err(SseAbortedError)
        return Err(SseNetworkError(fetchResult.unwrapErr()))
    }

    const response = fetchResult.unwrap()

    if (!response.ok) {
        const text = await response.text()
        return Err(SseHttpError(response.status, text))
    }

    const bodyOpt = fromNullable(response.body)
    if (bodyOpt.isNone()) return Err(SseNoBodyError)

    const parser = createParser({ onEvent: handlers.onEvent })
    const reader = bodyOpt.unwrap().getReader()
    const decoder = new TextDecoder()

    try {
        while (true) {
            const { done, value } = await reader.read()
            if (done) break
            parser.feed(decoder.decode(value, { stream: true }))
        }
    } catch (e) {
        if (signal?.aborted) {
            reader.releaseLock()
            return Err(SseAbortedError)
        }
        reader.releaseLock()
        return Err(SseStreamError(e instanceof Error ? e : new Error(String(e))))
    }

    reader.releaseLock()
    if (handlers.onClose.isSome()) handlers.onClose.unwrap()()
    return Ok(undefined)
}

// ─── Re-exports for ergonomics at call sites ─────────────────

export { Some, None }
