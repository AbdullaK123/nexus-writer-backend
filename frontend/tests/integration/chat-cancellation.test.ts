import { describe, expect, test, vi } from "vitest"

import { streamSse, None } from "../../src/infrastructure/sse"
import { beginChatTurn, buildChatTurnRequest, finishChatTurn } from "../../src/infrastructure/chat-stream"
import { AbortControllerSlot } from "../../src/shared/abortControllerSlot"
import { SingleFlightGate } from "../../src/shared/singleFlight"

function abortableFetch(): typeof fetch {
    return vi.fn((_input: RequestInfo | URL, init?: RequestInit) => {
        return new Promise<Response>((_resolve, reject) => {
            const signal = init?.signal
            if (!signal) return

            if (signal.aborted) {
                reject(new DOMException("Aborted", "AbortError"))
                return
            }

            signal.addEventListener(
                "abort",
                () => reject(new DOMException("Aborted", "AbortError")),
                { once: true },
            )
        })
    }) as typeof fetch
}

describe("chat cancellation integration", () => {
    test("teardown aborts the live chat request as an expected cancellation", async () => {
        const gate = new SingleFlightGate()
        const slot = new AbortControllerSlot()
        const controller = beginChatTurn(gate, slot)
        expect(controller).not.toBeNull()

        vi.stubGlobal("fetch", abortableFetch())

        const stream = streamSse(
            buildChatTurnRequest(
                "story-1",
                "thread-1",
                "hello",
                controller!.signal,
            ),
            { onEvent: vi.fn(), onClose: None },
        )

        slot.abort()
        const result = await stream
        finishChatTurn(gate)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr()).toEqual({ _tag: "SseAbortedError" })
        expect(gate.isActive).toBe(false)
        expect(slot.current).toBeNull()
    })
})
