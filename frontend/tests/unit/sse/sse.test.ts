import { beforeEach, describe, expect, test, vi } from "vitest"

import { isRetryable, isTerminal } from "../../../src/infrastructure/sse/notifications"
import type { SseError } from "../../../src/infrastructure/sse"

function streamFromChunks(chunks: string[]): ReadableStream<Uint8Array> {
    const encoder = new TextEncoder()
    return new ReadableStream({
        start(controller) {
            for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
            controller.close()
        },
    })
}

async function loadSse() {
    vi.stubEnv("VITE_API_BASE_URL", "http://api.test/api")
    vi.stubEnv("VITE_API_TIMEOUT_MS", "5000")
    vi.resetModules()
    return import("../../../src/infrastructure/sse")
}

beforeEach(() => {
    vi.restoreAllMocks()
})

describe("SSE retry classification", () => {
    test.each([
        { _tag: "SseNetworkError", cause: new Error("offline") },
        { _tag: "SseStreamError", cause: new Error("broken") },
        { _tag: "SseNoBodyError" },
        { _tag: "SseHttpError", status: 500, body: "boom" },
        { _tag: "SseHttpError", status: 429, body: "slow down" },
    ] satisfies SseError[])("retries transient failures", (error) => {
        expect(isRetryable(error)).toBe(true)
        expect(isTerminal(error)).toBe(false)
    })

    test.each([
        { _tag: "SseAbortedError" },
        { _tag: "SseHttpError", status: 401, body: "unauthorized" },
        { _tag: "SseHttpError", status: 403, body: "forbidden" },
        { _tag: "SseHttpError", status: 404, body: "gone" },
    ] satisfies SseError[])("stops on terminal failures", (error) => {
        expect(isTerminal(error)).toBe(true)
        expect(isRetryable(error)).toBe(false)
    })

    test("does not retry ordinary 4xx failures", () => {
        const error: SseError = { _tag: "SseHttpError", status: 422, body: "bad request" }

        expect(isRetryable(error)).toBe(false)
        expect(isTerminal(error)).toBe(false)
    })
})

describe("streamSse", () => {
    test("parses an event split across network chunks exactly once", async () => {
        const { streamSse, None, Some } = await loadSse()
        const onEvent = vi.fn()
        const onClose = vi.fn()

        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response(
                streamFromChunks([
                    "event: notification\nda",
                    "ta: {\"kind\":\"analysis_ready\"}\n\n",
                ]),
                { status: 200, headers: { "Content-Type": "text/event-stream" } },
            ),
        ))

        const result = await streamSse(
            {
                url: "events",
                method: Some("GET"),
                body: None,
                headers: None,
                signal: None,
            },
            { onEvent, onClose: Some(onClose) },
        )

        expect(result.isOk()).toBe(true)
        expect(onEvent).toHaveBeenCalledOnce()
        expect(onEvent).toHaveBeenCalledWith(
            expect.objectContaining({
                event: "notification",
                data: '{"kind":"analysis_ready"}',
            }),
        )
        expect(onClose).toHaveBeenCalledOnce()
    })

    test("returns the HTTP status and body without parsing a failed stream", async () => {
        const { streamSse, None, Some } = await loadSse()
        const onEvent = vi.fn()
        vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
            new Response("Authentication required", { status: 401 }),
        ))

        const result = await streamSse(
            {
                url: "events",
                method: Some("GET"),
                body: None,
                headers: None,
                signal: None,
            },
            { onEvent, onClose: None },
        )

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr()).toEqual({
            _tag: "SseHttpError",
            status: 401,
            body: "Authentication required",
        })
        expect(onEvent).not.toHaveBeenCalled()
    })

    test("classifies a fetch rejection as aborted when the caller aborted", async () => {
        const { streamSse, None, Some } = await loadSse()
        const controller = new AbortController()
        controller.abort()
        vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new DOMException("aborted", "AbortError")))

        const result = await streamSse(
            {
                url: "events",
                method: Some("GET"),
                body: None,
                headers: None,
                signal: Some(controller.signal),
            },
            { onEvent: vi.fn(), onClose: None },
        )

        expect(result.unwrapErr()).toEqual({ _tag: "SseAbortedError" })
    })

    test("classifies an un-aborted fetch rejection as a network error", async () => {
        const { streamSse, None, Some } = await loadSse()
        vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")))

        const result = await streamSse(
            {
                url: "events",
                method: Some("GET"),
                body: None,
                headers: None,
                signal: None,
            },
            { onEvent: vi.fn(), onClose: None },
        )

        expect(result.unwrapErr()).toEqual(
            expect.objectContaining({ _tag: "SseNetworkError" }),
        )
    })

    test("sends JSON bodies and cookies on POST streams", async () => {
        const { streamSse, None, Some } = await loadSse()
        const fetchMock = vi.fn().mockResolvedValue(
            new Response(streamFromChunks([]), { status: 200 }),
        )
        vi.stubGlobal("fetch", fetchMock)

        await streamSse(
            {
                url: "chat",
                method: Some("POST"),
                body: Some({ userMessage: "hello" }),
                headers: None,
                signal: None,
            },
            { onEvent: vi.fn(), onClose: None },
        )

        expect(fetchMock).toHaveBeenCalledWith(
            "http://api.test/api/chat",
            expect.objectContaining({
                method: "POST",
                body: JSON.stringify({ userMessage: "hello" }),
                credentials: "include",
                headers: expect.objectContaining({
                    Accept: "text/event-stream",
                    "Content-Type": "application/json",
                }),
            }),
        )
    })
})
