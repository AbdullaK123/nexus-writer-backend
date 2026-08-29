import { afterEach, describe, expect, test, vi } from "vitest"

import { None, Some, streamSse } from "../../src/infrastructure/sse"
import { createSseLifecycleCleanup } from "../../src/infrastructure/sse/lifecycle"
import { AbortControllerSlot } from "../../src/shared/abortControllerSlot"

afterEach(() => {
    vi.useRealTimers()
})

function abortableFetch(): typeof fetch {
    return vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        return new Promise<Response>((_resolve, reject) => {
            const signal = init?.signal
            if (!signal) return
            signal.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
            )
        })
    }) as typeof fetch
}

describe("notification teardown integration", () => {
    test("auth teardown aborts the live stream and cancels a queued reconnect", async () => {
        vi.useFakeTimers()
        vi.stubGlobal("fetch", abortableFetch())

        const slot = new AbortControllerSlot()
        const controller = slot.replace()
        const stoppedRef = { current: false }
        const reconnect = vi.fn()
        const timerRef = {
            current: setTimeout(reconnect, 1_000) as unknown as number,
        }

        const stream = streamSse(
            {
                url: "auth/me/notifications",
                method: Some("GET"),
                body: None,
                headers: None,
                signal: Some(controller.signal),
            },
            { onEvent: vi.fn(), onClose: None },
        )

        const cleanup = createSseLifecycleCleanup(
            slot,
            timerRef,
            stoppedRef,
            (id) => clearTimeout(id),
        )
        cleanup()

        const result = await stream
        await vi.advanceTimersByTimeAsync(1_000)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr()).toEqual({ _tag: "SseAbortedError" })
        expect(stoppedRef.current).toBe(true)
        expect(slot.current).toBeNull()
        expect(timerRef.current).toBeNull()
        expect(reconnect).not.toHaveBeenCalled()
    })
})
