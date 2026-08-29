import { describe, expect, test } from "vitest"
import type { EventSourceMessage } from "eventsource-parser"

import { decodeChatStreamToken } from "../../../src/infrastructure/chat-stream"

function event(event: string, data: string): EventSourceMessage {
    return { id: "", event, data }
}

describe("chat stream adversarial event decoding", () => {
    test("server error event is never treated like an ignorable successful close", () => {
        expect(() =>
            decodeChatStreamToken(
                event("error", JSON.stringify({
                    code: "INTERNAL",
                    message: "The turn failed after streaming began",
                })),
            ),
        ).toThrow()
    })

    test("token event requires a string delta", () => {
        expect(() =>
            decodeChatStreamToken(event("token", JSON.stringify({ delta: 42 }))),
        ).toThrow()

        expect(() =>
            decodeChatStreamToken(event("token", JSON.stringify({ nope: "missing" }))),
        ).toThrow()
    })

    test("malformed token json fails closed", () => {
        expect(() => decodeChatStreamToken(event("token", "{not-json"))).toThrow()
    })

    test("unknown protocol events remain ignorable", () => {
        expect(decodeChatStreamToken(event("heartbeat", "{}"))).toBeNull()
    })
})
