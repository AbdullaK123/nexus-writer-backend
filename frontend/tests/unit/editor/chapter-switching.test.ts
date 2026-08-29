import { describe, expect, test } from "vitest"

import { isCurrentChapter } from "../../../src/components/chapter/ChapterEditorPage/chapterIdentity"

describe("chapter switching", () => {
    test("accepts data for the currently routed chapter", () => {
        expect(isCurrentChapter("chapter-2", "chapter-2")).toBe(true)
    })

    test("rejects stale data from the previously routed chapter", () => {
        expect(isCurrentChapter("chapter-2", "chapter-1")).toBe(false)
    })
})
