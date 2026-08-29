import { MutationObserver } from "@tanstack/react-query"
import { describe, expect, test, vi } from "vitest"

import type { AppApi } from "../../src/infrastructure/api"
import type { ChapterContentResponse } from "../../src/infrastructure/api/types"
import { createUpdateChapterMutationOptions, chapterKeys } from "../../src/data/queries/chapter"
import { ApiError, Err, Ok, type Result } from "../../src/shared/types"
import { createIntegrationQueryClient, deferred } from "./harness"

function chapter(overrides: Partial<ChapterContentResponse> = {}): ChapterContentResponse {
    return {
        id: "chapter-1",
        storyId: "story-1",
        storyTitle: "Story",
        title: "Chapter One",
        content: "<p>Original body</p>",
        published: false,
        chapterNumber: 1,
        wordCount: 2,
        createdAt: new Date("2026-01-01T00:00:00Z"),
        updatedAt: new Date("2026-01-01T00:00:00Z"),
        previousChapterId: null,
        nextChapterId: "chapter-2",
        ...overrides,
    }
}

function apiWithUpdate(
    updateChapter: AppApi["chapter"]["updateChapter"],
): AppApi {
    return {
        chapter: { updateChapter } as AppApi["chapter"],
    } as AppApi
}

describe("chapter autosave integration", () => {
    test("a partial update preserves untouched cached chapter content while the save is in flight", async () => {
        const qc = createIntegrationQueryClient()
        const pending = deferred<Result<ChapterContentResponse, ApiError>>()
        const updateChapter = vi.fn(() => pending.promise) as AppApi["chapter"]["updateChapter"]
        const api = apiWithUpdate(updateChapter)
        const key = chapterKeys.detail("chapter-1", true)
        qc.setQueryData(key, chapter())

        const observer = new MutationObserver(
            qc,
            createUpdateChapterMutationOptions(api, qc, "chapter-1"),
        )

        const mutation = observer.mutate({ title: "Renamed" })
        await vi.waitFor(() => {
            expect(updateChapter).toHaveBeenCalledOnce()
        })

        expect(qc.getQueryData<ChapterContentResponse>(key)).toMatchObject({
            title: "Renamed",
            content: "<p>Original body</p>",
        })
        expect(updateChapter).toHaveBeenCalledWith("chapter-1", { title: "Renamed" })

        pending.resolve(Ok(chapter({ title: "Renamed" })))
        await mutation
    })

    test("a failed autosave rolls the optimistic cache back to the exact previous chapter", async () => {
        const qc = createIntegrationQueryClient()
        const pending = deferred<Result<ChapterContentResponse, ApiError>>()
        const updateChapter = vi.fn(() => pending.promise) as AppApi["chapter"]["updateChapter"]
        const api = apiWithUpdate(updateChapter)
        const key = chapterKeys.detail("chapter-1", true)
        const original = chapter()
        qc.setQueryData(key, original)

        const observer = new MutationObserver(
            qc,
            createUpdateChapterMutationOptions(api, qc, "chapter-1"),
        )

        const mutation = observer.mutate({ content: "<p>Unsaved edit</p>" })
        await vi.waitFor(() => {
            expect(updateChapter).toHaveBeenCalledOnce()
        })

        expect(qc.getQueryData<ChapterContentResponse>(key)?.content).toBe("<p>Unsaved edit</p>")

        const failure = new ApiError(500, "Save failed")
        pending.resolve(Err(failure))
        await expect(mutation).rejects.toBe(failure)

        expect(qc.getQueryData<ChapterContentResponse>(key)).toEqual(original)
    })
})
