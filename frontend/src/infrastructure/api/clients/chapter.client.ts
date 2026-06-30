import { ApiClient } from "./base.client"
import {
    type UpdateChapterRequest,
    type ChapterContentResponse,
    ChapterContentResponseSchema,
    type ApiMessage,
    ApiMessageSchema,
    type RequestOptions,
    noRequestOptions,
    type ChapterSummaryResponse,
    ChapterSummaryResponseSchema,
} from "../types"
import type { Result, ApiError } from "../../../shared/types"

export class ChapterClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public getChapter(
        chapterId: string,
        asHtml: boolean = true,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ChapterContentResponse, ApiError>> {
        return this.api.getJson(
            `chapters/${chapterId}?as_html=${asHtml}`,
            ChapterContentResponseSchema,
            options,
        )
    }

    public updateChapter(
        chapterId: string,
        payload: UpdateChapterRequest,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ChapterContentResponse, ApiError>> {
        return this.api.putJson(
            `chapters/${chapterId}`,
            payload,
            ChapterContentResponseSchema,
            options,
        )
    }

    public deleteChapter(
        chapterId: string,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ApiMessage, ApiError>> {
        return this.api.deleteJson(
            `chapters/${chapterId}`,
            ApiMessageSchema,
            options,
        )
    }

    public summarizeChapter(
        chapterId: string,
        options: RequestOptions = noRequestOptions,
    ): Promise<Result<ChapterSummaryResponse, ApiError>> {
        console.log("GOTCHA")
        return this.api.getJson(
            `chapters/${chapterId}/summary`,
            ChapterSummaryResponseSchema,
            options
        )
    }
}
