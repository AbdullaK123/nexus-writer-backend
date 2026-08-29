import { None, Some, type SseRequest } from "./sse"

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

export function completeChatTurn(refreshMessages: () => void): void {
    refreshMessages()
}
