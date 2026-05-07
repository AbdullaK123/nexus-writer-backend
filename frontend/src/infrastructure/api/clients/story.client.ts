import { ApiClient } from "./base.client"
import { 
    type CreateStoryRequest, 
    ApiMessageSchema, 
    type ApiMessage,
    type UpdateStoryRequest,
    type StoryGridResponse,
    StoryGridResponseSchema,
    type RequestOptions,
    type StoryDetailResponse,
    StoryDetailResponseSchema,
    type CreateChapterRequest,
    type ChapterContentResponse,
    ChapterContentResponseSchema,
    type ReorderChapterRequest,
    type SceneSearchRequest,
    type ChapterListResponse,
    ChapterListResponseSchema,
    type SceneSearchListResponse,
    SceneSearchListResponseSchema,
    type VocabularyListResponse,
    VocabularyListResponseSchema,
 } from "../types"
import { unwrapResult } from "../../../shared/types"

export class StoryClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public async createStory(
        payload: CreateStoryRequest,
        options: RequestOptions = {}
    ): Promise<ApiMessage> {
        const response  = await this.api.postJson(
            "/stories",
            payload,
            ApiMessageSchema,
            options
        )
        return unwrapResult(response)
    }

    public async updateStory(
        payload: UpdateStoryRequest,
        options: RequestOptions = {}
    ): Promise<ApiMessage> {
        const response = await this.api.putJson(
            "/stories",
            payload,
            ApiMessageSchema,
            options
        )
        return unwrapResult(response)
    }

    public async deleteStory(
        storyId: string,
        options: RequestOptions = {}
    ): Promise<ApiMessage> {
        const response = await this.api.deleteJson(
            `/stories/${storyId}`,
            ApiMessageSchema,
            options
        )
        return unwrapResult(response)
    }

    public async getStories(
        options: RequestOptions = {}
    ): Promise<StoryGridResponse> {
        const response = await this.api.getJson(
            "/stories",
            StoryGridResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async getStoryDetails(
        storyId: string,
        options: RequestOptions = {}
    ): Promise<StoryDetailResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}`,
            StoryDetailResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async createChapter(
        storyId: string,
        payload: CreateChapterRequest,
        options: RequestOptions = {}
    ): Promise<ChapterContentResponse> {
        const response = await this.api.postJson(
            `/stories/${storyId}/chapters`,
            payload,
            ChapterContentResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async reorderChapters(
        storyId: string,
        payload: ReorderChapterRequest,
        options: RequestOptions = {}
    ): Promise<ApiMessage> {
        const response = await this.api.postJson(
            `/stories/${storyId}/chapters/reorder`,
            payload,
            ApiMessageSchema,
            options
        )
        return unwrapResult(response)
    }

    public async getStoryChapters(
        storyId: string,
        options: RequestOptions = {}
    ): Promise<ChapterListResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}/chapters`,
            ChapterListResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async searchStoryScenes(
        storyId: string,
        payload: SceneSearchRequest,
        options: RequestOptions = {}
    ): Promise<SceneSearchListResponse> {
        const response = await this.api.postJson(
            `/stories/${storyId}/search`,
            payload,
            SceneSearchListResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async listStoryTags(
        storyId: string,
        options: RequestOptions = {}
    ): Promise<VocabularyListResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}/tags`,
            VocabularyListResponseSchema,
            options
        )
        return unwrapResult(response)
    }

    public async listStoryEntities(
        storyId: string,
        options: RequestOptions = {}
    ): Promise<VocabularyListResponse> {
        const response = await this.api.getJson(
            `/stories/${storyId}/entities`,
            VocabularyListResponseSchema,
            options
        )
        return unwrapResult(response)
    }
}