import { describe, expect, test } from "vitest"

import { buildReorderRequest } from "../../../src/components/chapter/ChapterEditorPage/ChapterEditorSidebar/reorder"

describe("buildReorderRequest", () => {
    test.each([
        [0, 4, 5, { fromPos: 0, toPos: 4 }],
        [4, 0, 5, { fromPos: 4, toPos: 0 }],
        [1, 2, 5, { fromPos: 1, toPos: 2 }],
    ] as const)("accepts valid move %i -> %i", (fromPos, toPos, count, expected) => {
        expect(buildReorderRequest(fromPos, toPos, count)).toEqual(expected)
    })

    test.each([
        [2, 2, 5],
        [-1, 2, 5],
        [1, -1, 5],
        [5, 1, 5],
        [1, 5, 5],
        [1.5, 2, 5],
    ])("rejects invalid/no-op move %s -> %s", (fromPos, toPos, count) => {
        expect(buildReorderRequest(fromPos, toPos, count)).toBeNull()
    })
})
