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

/** Preserve the hook's current event semantics behind a testable boundary. */
export function decodeChatStreamToken(event: EventSourceMessage): string | null {
    if (event.event !== "token") return null
    const data = JSON.parse(event.data) as { delta?: string }
    return data.delta ?? null
}
