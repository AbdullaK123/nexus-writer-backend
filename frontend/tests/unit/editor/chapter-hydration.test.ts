import { describe, expect, test, vi } from "vitest"

import { hydrateChapterContent } from "../../../src/components/chapter/ChapterEditorPage/chapterHydration"

describe("chapter editor hydration", () => {
    test("loading canonical server content does not emit a user update", () => {
        const setContent = vi.fn(() => true)

        hydrateChapterContent(
            { commands: { setContent } },
            "<p>Canonical server content</p>",
        )

        expect(setContent).toHaveBeenCalledOnce()
        expect(setContent).toHaveBeenCalledWith(
            "<p>Canonical server content</p>",
            { emitUpdate: false },
        )
    })
})
