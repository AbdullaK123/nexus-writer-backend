import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../../infrastructure/api"
import type {
    CreateThreadBody,
    RenameThreadBody,
} from "../../infrastructure/api/types"

// ─── Keys ──────────────────────────────────────────────────────────────────
// Threads are story-scoped; messages are thread-scoped. Hierarchy makes
// it cheap to wipe the whole story chat tree on story deletion, while
// still allowing surgical message-list invalidation after each turn.

export const chatKeys = {
    all: ["chat"] as const,
    threads: (storyId: string) =>
        [...chatKeys.all, "threads", storyId] as const,
    messages: (storyId: string, threadId: string) =>
        [...chatKeys.threads(storyId), threadId, "messages"] as const,
}

// ─── Queries ───────────────────────────────────────────────────────────────

export function useThreads(storyId: string) {
    return useQuery({
        queryKey: chatKeys.threads(storyId),
        queryFn: ({ signal }) => api.chat.getThreads(storyId, { signal }),
        enabled: Boolean(storyId),
    })
}

export function useThreadMessages(storyId: string, threadId: string) {
    return useQuery({
        queryKey: chatKeys.messages(storyId, threadId),
        queryFn: ({ signal }) =>
            api.chat.getThreadMessages(storyId, threadId, { signal }),
        enabled: Boolean(storyId) && Boolean(threadId),
    })
}

// ─── Mutations ─────────────────────────────────────────────────────────────
// Streaming the assistant turn is intentionally NOT a TanStack mutation
// — it's an SSE stream owned by `useChatStream`. After the stream
// finishes, that hook should invalidate `chatKeys.messages(...)` so the
// canonical persisted message list refetches.

export function useCreateThread(storyId: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateThreadBody) =>
            api.chat.createThread(storyId, payload),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}

export function useRenameThread(storyId: string, threadId: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: RenameThreadBody) =>
            api.chat.renameThread(storyId, threadId, payload),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}

export function useDeleteThread(storyId: string, threadId: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: () => api.chat.deleteThread(storyId, threadId),
        onSuccess: () => {
            qc.removeQueries({
                queryKey: chatKeys.messages(storyId, threadId),
            })
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}