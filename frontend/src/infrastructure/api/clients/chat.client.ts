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
} from "../types"
import { unwrapResult } from "../../../shared/types"

export class ChatClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public async createThread(
        storyId: string,
        payload: CreateThreadBody,
        options: RequestOptions = {},
    ): Promise<ThreadResponse> {
        const response = await this.api.postJson(
            `/stories/${storyId}/chat/threads`,
            payload,
            ThreadResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async getThreads(
        storyId: string,
        options: RequestOptions = {},
    ): Promise<ThreadListResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}/chat/threads`,
            ThreadListResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async getThreadMessages(
        storyId: string,
        threadId: string,
        options: RequestOptions = {},
    ): Promise<ChatMessageListResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}/chat/threads/${threadId}/messages`,
            ChatMessageListResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async renameThread(
        storyId: string,
        threadId: string,
        payload: RenameThreadBody,
        options: RequestOptions = {},
    ): Promise<ThreadResponse> {
        const response = await this.api.patchJson(
            `/stories/${storyId}/chat/threads/${threadId}`,
            payload,
            ThreadResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async deleteThread(
        storyId: string,
        threadId: string,
        options: RequestOptions = {},
    ): Promise<ApiMessage> {
        const response = await this.api.deleteJson(
            `/stories/${storyId}/chat/threads/${threadId}`,
            ApiMessageSchema,
            options,
        )
        return unwrapResult(response)
    }
}
