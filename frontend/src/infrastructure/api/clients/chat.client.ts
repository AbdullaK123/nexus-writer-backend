import { ApiClient } from "./base.client"
import {
    type CreateThreadBody,
    type RenameThreadBody,
    type ThreadResponse,
    ThreadResponseSchema,
    type ThreadListResponse,
    ThreadListResponseSchema,
    type ChatMessageListResponse,
    ChatMessageListResponseSchema,
    type ApiMessage,
    ApiMessageSchema,
    type RequestOptions,
    noRequestOptions,
} from "../types"
import type { Result, ApiError } from "../../../shared/types"

export class ChatClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public createThread(
        storyId: string,
        payload: CreateThreadBody,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ThreadResponse, ApiError>> {
        return this.api.postJson(
            `/stories/${storyId}/chat/threads`,
            payload,
            ThreadResponseSchema,
            options,
        )
    }

    public getThreads(
        storyId: string,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ThreadListResponse, ApiError>> {
        return this.api.getJson(
            `/stories/${storyId}/chat/threads`,
            ThreadListResponseSchema,
            options,
        )
    }

    public getThreadMessages(
        storyId: string,
        threadId: string,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ChatMessageListResponse, ApiError>> {
        return this.api.getJson(
            `/stories/${storyId}/chat/threads/${threadId}/messages`,
            ChatMessageListResponseSchema,
            options,
        )
    }

    public renameThread(
        storyId: string,
        threadId: string,
        payload: RenameThreadBody,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ThreadResponse, ApiError>> {
        return this.api.patchJson(
            `/stories/${storyId}/chat/threads/${threadId}`,
            payload,
            ThreadResponseSchema,
            options,
        )
    }

    public deleteThread(
        storyId: string,
        threadId: string,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.deleteJson(
            `/stories/${storyId}/chat/threads/${threadId}`,
            ApiMessageSchema,
            options,
        )
    }
}
