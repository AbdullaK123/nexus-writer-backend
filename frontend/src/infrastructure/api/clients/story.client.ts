import { ApiClient } from "./base.client"
import { 
    type CreateStoryRequest, 
    ApiMessageSchema, 
    type ApiMessage,
    type UpdateStoryRequest,
    type StoryGridResponse,
    StoryGridResponseSchema,
    type RequestOptions,
    noRequestOptions,
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
    type BookPulseResponse,
    BookPulseResponseSchema,
    type StoryStatsResponse,
    StoryStatsResponseSchema,
    type StoryPathArrayResponse,
    StoryPathArrayResponseSchema,
 } from "../types"
import type { Result, ApiError } from "../../../shared/types"
import { CharacterDashboardResponseSchema, PlotDashboardResponseSchema, StructureDashboardResponseSchema, WorldDashboardResponseSchema, type CharacterDashboardResponse, type PlotDashboardResponse, type StructureDashboardResponse, type WorldDashboardResponse } from "../types/analytics";

export class StoryClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public getPathArray(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StoryPathArrayResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/path`,
            StoryPathArrayResponseSchema,
            options
        )
    }

    public createStory(
        payload: CreateStoryRequest,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.postJson(
            "stories",
            payload,
            ApiMessageSchema,
            options
        )
    }

    public updateStory(
        payload: UpdateStoryRequest,
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.putJson(
            `stories/${storyId}`,
            payload,
            ApiMessageSchema,
            options
        )
    }

    public deleteStory(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.deleteJson(
            `stories/${storyId}`,
            ApiMessageSchema,
            options
        )
    }

    public getStories(
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StoryGridResponse, ApiError>> {
        return this.api.getJson(
            "stories",
            StoryGridResponseSchema,
            options
        )
    }

    public getStoryDetails(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StoryDetailResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}`,
            StoryDetailResponseSchema,
            options
        )
    }

    public createChapter(
        storyId: string,
        payload: CreateChapterRequest,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ChapterContentResponse, ApiError>> {
        return this.api.postJson(
            `stories/${storyId}/chapters`,
            payload,
            ChapterContentResponseSchema,
            options
        )
    }

    public reorderChapters(
        storyId: string,
        payload: ReorderChapterRequest,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.postJson(
            `stories/${storyId}/chapters/reorder`,
            payload,
            ApiMessageSchema,
            options
        )
    }

    public getStoryChapters(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<ChapterListResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/chapters`,
            ChapterListResponseSchema,
            options
        )
    }

    public searchStoryScenes(
        storyId: string,
        payload: SceneSearchRequest,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<SceneSearchListResponse, ApiError>> {
        return this.api.postJson(
            `stories/${storyId}/search`,
            payload,
            SceneSearchListResponseSchema,
            options
        )
    }

    public listStoryTags(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<VocabularyListResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/tags`,
            VocabularyListResponseSchema,
            options
        )
    }

    public listStoryEntities(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<VocabularyListResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/entities`,
            VocabularyListResponseSchema,
            options
        )
    }

    public getPulse(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<BookPulseResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/pulse`,
            BookPulseResponseSchema,
            options
        )
    }

    public getStats(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StoryStatsResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/stats`,
            StoryStatsResponseSchema,
            options
        )
    }

    public getCharacterDashboard(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<CharacterDashboardResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/analytics/dashboard/characters`,
            CharacterDashboardResponseSchema,
            options
        )
    }

    public getPlotDashboard(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<PlotDashboardResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/analytics/dashboard/plot`,
            PlotDashboardResponseSchema,
            options
        )
    }

    public getStuctureDashboard(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<StructureDashboardResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/analytics/dashboard/structure`,
            StructureDashboardResponseSchema,
            options
        )
    }


    public getWorldDashboard(
        storyId: string,
        options: RequestOptions = noRequestOptions
    ): Promise<Result<WorldDashboardResponse, ApiError>> {
        return this.api.getJson(
            `stories/${storyId}/analytics/dashboard/world`,
            WorldDashboardResponseSchema,
            options
        )
    }
}