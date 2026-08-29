import { useQuery, useMutation, useQueryClient, type QueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type ChatMessageListResponse,
    type CreateThreadBody,
    type RenameThreadBody,
    requestOptions,
    type ThreadListResponse,
} from "../../infrastructure/api/types"
import type { AppApi } from "../../infrastructure/api"
import { ApiError, unwrapResultAsync } from "../../shared/types"
import { toAsyncState } from "../../infrastructure/api/utils";
import { useNavigate } from "@tanstack/react-router";

export const chatKeys = {
    all: ["chat"] as const,
    threads: (storyId: string) =>
        [...chatKeys.all, "threads", storyId] as const,
    messages: (storyId: string, threadId: string) =>
        [...chatKeys.threads(storyId), threadId, "messages"] as const,
}

export function useThreads(storyId: string) {
    const api = useApi()
    const response = useQuery<ThreadListResponse, ApiError>({
        queryKey: chatKeys.threads(storyId),
        queryFn: ({ signal }) => unwrapResultAsync(api.chat.getThreads(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
    return toAsyncState<ThreadListResponse>(response)
}

export function useThreadMessages(storyId: string, threadId: string) {
    const api = useApi()
    const response = useQuery<ChatMessageListResponse, ApiError>({
        queryKey: chatKeys.messages(storyId, threadId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.chat.getThreadMessages(storyId, threadId, requestOptions({ signal }))),
        enabled: Boolean(storyId) && Boolean(threadId),
    })
    return [toAsyncState<ChatMessageListResponse>(response), response.refetch] as const
}

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

export type ThreadDeleteNavigate = (navigation: {
    to: "/stories/$storyId/chat/new"
    params: { storyId: string }
}) => Promise<unknown> | unknown

export function createDeleteThreadMutationOptions(
    api: AppApi,
    qc: QueryClient,
    navigate: ThreadDeleteNavigate,
    storyId: string,
    threadId: string,
) {
    return {
        mutationFn: () => unwrapResultAsync(api.chat.deleteThread(storyId, threadId)),
        onSuccess: async () => {
            qc.removeQueries({
                queryKey: chatKeys.messages(storyId, threadId),
            })
            await qc.invalidateQueries({ queryKey: chatKeys.threads(storyId) })
            await navigate({
                to: "/stories/$storyId/chat/new",
                params: { storyId },
            })
        },
    }
}

export function useDeleteThread(storyId: string, threadId: string) {
    const api = useApi()
    const qc = useQueryClient()
    const navigate = useNavigate()
    return useMutation(
        createDeleteThreadMutationOptions(api, qc, navigate, storyId, threadId),
    )
}
