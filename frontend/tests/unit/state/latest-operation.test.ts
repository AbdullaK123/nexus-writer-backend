import { describe, expect, test } from "vitest"

import { LatestOperation } from "../../../src/shared/latestOperation"

describe("LatestOperation", () => {
    test("only the newest operation remains current", () => {
        const tracker = new LatestOperation()
        const first = tracker.start()
        const second = tracker.start()

        expect(tracker.isLatest(first)).toBe(false)
        expect(tracker.isLatest(second)).toBe(true)
    })

    test("invalidate makes outstanding completions stale", () => {
        const tracker = new LatestOperation()
        const revision = tracker.start()

        tracker.invalidate()

        expect(tracker.isLatest(revision)).toBe(false)
    })
})
