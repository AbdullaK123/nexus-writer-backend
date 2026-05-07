import { ApiClient } from "./base.client"
import {
    type UpdateChapterRequest,
    type ChapterContentResponse,
    ChapterContentResponseSchema,
    type ApiMessage,
    ApiMessageSchema,
    type RequestOptions,
} from "../types"
import { unwrapResult } from "../../../shared/types"

export class ChapterClient {

    private readonly api: ApiClient
    constructor(api: ApiClient) {
        this.api = api
    }

    public async getChapter(
        chapterId: string,
        asHtml: boolean = true,
        options: RequestOptions = {},
    ): Promise<ChapterContentResponse> {
        const response = await this.api.getJson(
            `/chapters/${chapterId}?as_html=${asHtml}`,
            ChapterContentResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async updateChapter(
        chapterId: string,
        payload: UpdateChapterRequest,
        options: RequestOptions = {},
    ): Promise<ChapterContentResponse> {
        const response = await this.api.putJson(
            `/chapters/${chapterId}`,
            payload,
            ChapterContentResponseSchema,
            options,
        )
        return unwrapResult(response)
    }

    public async deleteChapter(
        chapterId: string,
        options: RequestOptions = {},
    ): Promise<ApiMessage> {
        const response = await this.api.deleteJson(
            `/chapters/${chapterId}`,
            ApiMessageSchema,
            options,
        )
        return unwrapResult(response)
    }
}
