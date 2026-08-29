import { describe, expect, test, vi } from "vitest"

import {
    buildChatTurnRequest,
    completeChatTurn,
} from "../../../src/infrastructure/chat-stream"

describe("chat turn streaming", () => {
    test("builds the exact backend turn route and camelCase request body", () => {
        const controller = new AbortController()

        const request = buildChatTurnRequest(
            "story-1",
            "thread-2",
            "What happens next?",
            controller.signal,
        )

        expect(request.url).toBe("stories/story-1/chat/threads/thread-2/turn")
        expect(request.method.unwrap()).toBe("POST")
        expect(request.body.unwrap()).toEqual({
            userMessage: "What happens next?",
        })
        expect(request.signal.unwrap()).toBe(controller.signal)
        expect(request.headers.isNone()).toBe(true)
    })

    test("does not leak snake_case into the HTTP body", () => {
        const request = buildChatTurnRequest(
            "story-1",
            "thread-2",
            "hello",
            new AbortController().signal,
        )

        expect(request.body.unwrap()).not.toHaveProperty("user_message")
    })

    test("successful stream completion refreshes canonical persisted messages", () => {
        const refreshMessages = vi.fn()

        completeChatTurn(refreshMessages)

        expect(refreshMessages).toHaveBeenCalledOnce()
    })
})
