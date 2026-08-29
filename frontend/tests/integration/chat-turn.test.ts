import { describe, expect, test, vi } from "vitest"

import { streamSse, Some } from "../../src/infrastructure/sse"
import {
    beginChatTurn,
    buildChatTurnRequest,
    completeChatTurn,
    finishChatTurn,
} from "../../src/infrastructure/chat-stream"
import { AbortControllerSlot } from "../../src/shared/abortControllerSlot"
import { SingleFlightGate } from "../../src/shared/singleFlight"

function sseResponse(chunks: string[]): Response {
    const encoder = new TextEncoder()
    return new Response(
        new ReadableStream<Uint8Array>({
            start(controller) {
                for (const chunk of chunks) controller.enqueue(encoder.encode(chunk))
                controller.close()
            },
        }),
        {
            status: 200,
            headers: { "Content-Type": "text/event-stream" },
        },
    )
}

describe("chat turn integration", () => {
    test("a turn flows through the real SSE transport and refreshes persisted messages on close", async () => {
        const gate = new SingleFlightGate()
        const slot = new AbortControllerSlot()
        const controller = beginChatTurn(gate, slot)
        expect(controller).not.toBeNull()

        const fetchMock = vi.fn().mockResolvedValue(
            sseResponse([
                "event: token\ndata: {\"delta\":\"Hello \"}\n\n",
                "event: token\ndata: {\"delta\":\"world\"}\n\n",
            ]),
        )
        vi.stubGlobal("fetch", fetchMock)

        const deltas: string[] = []
        const refreshMessages = vi.fn()
        const result = await streamSse(
            buildChatTurnRequest(
                "story-1",
                "thread-1",
                "Say hello",
                controller!.signal,
            ),
            {
                onEvent: (event) => {
                    if (event.event === "token") {
                        deltas.push(JSON.parse(event.data).delta as string)
                    }
                },
                onClose: Some(() => {
                    finishChatTurn(gate)
                    completeChatTurn(refreshMessages)
                }),
            },
        )

        expect(result.isOk()).toBe(true)
        expect(deltas.join("")).toBe("Hello world")
        expect(refreshMessages).toHaveBeenCalledOnce()
        expect(gate.isActive).toBe(false)
        expect(fetchMock).toHaveBeenCalledOnce()

        const [, init] = fetchMock.mock.calls[0] as [string, RequestInit]
        expect(init.body).toBe(JSON.stringify({ userMessage: "Say hello" }))
    })

    test("a second turn cannot start while the first turn owns the single-flight gate", () => {
        const gate = new SingleFlightGate()
        const slot = new AbortControllerSlot()

        const first = beginChatTurn(gate, slot)
        const second = beginChatTurn(gate, slot)

        expect(first).not.toBeNull()
        expect(second).toBeNull()
        expect(first?.signal.aborted).toBe(false)
    })
})
