import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type CreateThreadBody,
    type RenameThreadBody,
    requestOptions,
} from "../../infrastructure/api/types"
import { unwrapResultAsync } from "../../shared/types"

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
    const api = useApi()
    return useQuery({
        queryKey: chatKeys.threads(storyId),
        queryFn: ({ signal }) => unwrapResultAsync(api.chat.getThreads(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
}

export function useThreadMessages(storyId: string, threadId: string) {
    const api = useApi()
    return useQuery({
        queryKey: chatKeys.messages(storyId, threadId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.chat.getThreadMessages(storyId, threadId, requestOptions({ signal }))),
        enabled: Boolean(storyId) && Boolean(threadId),
    })
}

// ─── Mutations ─────────────────────────────────────────────────────────────
// Streaming the assistant turn is intentionally NOT a TanStack mutation
// — it's an SSE stream owned by `useChatStream`. After the stream
// finishes, that hook should invalidate `chatKeys.messages(...)` so the
// canonical persisted message list refetches.

export function useCreateThread(storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateThreadBody) =>
            unwrapResultAsync(api.chat.createThread(storyId, payload)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}

export function useRenameThread(storyId: string, threadId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: RenameThreadBody) =>
            unwrapResultAsync(api.chat.renameThread(storyId, threadId, payload)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}

export function useDeleteThread(storyId: string, threadId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: () => unwrapResultAsync(api.chat.deleteThread(storyId, threadId)),
        onSuccess: () => {
            qc.removeQueries({
                queryKey: chatKeys.messages(storyId, threadId),
            })
            qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
        },
    })
}