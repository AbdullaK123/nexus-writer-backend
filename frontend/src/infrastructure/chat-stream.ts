import type { EventSourceMessage } from "eventsource-parser"
import { None, Some, type SseRequest } from "./sse"
import { AbortControllerSlot } from "../shared/abortControllerSlot"
import { SingleFlightGate } from "../shared/singleFlight"

export function buildChatTurnRequest(
    storyId: string,
    threadId: string,
    userMessage: string,
    signal: AbortSignal,
): SseRequest {
    return {
        url: `stories/${storyId}/chat/threads/${threadId}/turn`,
        method: Some("POST"),
        body: Some({ userMessage }),
        signal: Some(signal),
        headers: None,
    }
}

export function beginChatTurn(
    gate: SingleFlightGate,
    slot: AbortControllerSlot,
): AbortController | null {
    if (!gate.tryStart()) return null
    return slot.replace()
}

export function finishChatTurn(gate: SingleFlightGate): void {
    gate.finish()
}

export function completeChatTurn(refreshMessages: () => void): void {
    refreshMessages()
}

/**
 * Decode one chat SSE event.
 *
 * `streamSse` treats exceptions from `onEvent` as stream failures, which is
 * exactly what we want for semantic `event:error` frames and malformed token
 * payloads: the hook must take its error path and must not run the clean-close
 * callback.
 */
export function decodeChatStreamToken(event: EventSourceMessage): string | null {
    if (event.event === "error") {
        let message = "Chat stream failed"
        try {
            const data = JSON.parse(event.data) as { message?: unknown; code?: unknown }
            if (typeof data.message === "string" && data.message.length > 0) {
                message = data.message
            } else if (typeof data.code === "string" && data.code.length > 0) {
                message = `Chat stream failed: ${data.code}`
            }
        } catch {
            message = "Chat stream returned a malformed error event"
        }
        throw new Error(message)
    }

    if (event.event !== "token") return null

    const data = JSON.parse(event.data) as { delta?: unknown }
    if (typeof data.delta !== "string") {
        throw new Error("Chat token event is missing a string delta")
    }
    return data.delta
}
