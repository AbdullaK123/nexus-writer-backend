import { describe, expect, test } from "vitest"

import type { ChapterContentResponse } from "../../src/infrastructure/api/types"
import { chapterKeys } from "../../src/data/queries/chapter"
import { isCurrentChapter } from "../../src/components/chapter/ChapterEditorPage/chapterIdentity"
import { createIntegrationQueryClient, deferred } from "./harness"

function chapter(id: string, content: string): ChapterContentResponse {
    return {
        id,
        storyId: "story-1",
        storyTitle: "Story",
        title: id,
        content,
        published: false,
        chapterNumber: id === "chapter-a" ? 1 : 2,
        wordCount: 1,
        createdAt: new Date("2026-01-01T00:00:00Z"),
        updatedAt: new Date("2026-01-01T00:00:00Z"),
        previousChapterId: null,
        nextChapterId: null,
    }
}

describe("chapter navigation race integration", () => {
    test("a late chapter A response cannot hydrate chapter B after navigation", async () => {
        const qc = createIntegrationQueryClient()
        const chapterA = deferred<ChapterContentResponse>()

        const aRequest = qc.fetchQuery({
            queryKey: chapterKeys.detail("chapter-a", true),
            queryFn: () => chapterA.promise,
        })

        const selectedChapterId = "chapter-b"
        const bResult = await qc.fetchQuery({
            queryKey: chapterKeys.detail("chapter-b", true),
            queryFn: async () => chapter("chapter-b", "<p>B</p>"),
        })

        expect(isCurrentChapter(selectedChapterId, bResult.id)).toBe(true)

        chapterA.resolve(chapter("chapter-a", "<p>A</p>"))
        const lateAResult = await aRequest

        expect(isCurrentChapter(selectedChapterId, lateAResult.id)).toBe(false)
        expect(qc.getQueryData(chapterKeys.detail("chapter-b", true))).toMatchObject({
            id: "chapter-b",
            content: "<p>B</p>",
        })
        expect(qc.getQueryData(chapterKeys.detail("chapter-a", true))).toMatchObject({
            id: "chapter-a",
            content: "<p>A</p>",
        })
    })
})
