import { describe, expect, test } from "vitest"

import { AbortControllerSlot } from "../../../src/shared/abortControllerSlot"

describe("AbortControllerSlot", () => {
    test("replacing a controller aborts the previous stream", () => {
        const slot = new AbortControllerSlot()
        const first = slot.replace()
        const second = slot.replace()

        expect(first.signal.aborted).toBe(true)
        expect(second.signal.aborted).toBe(false)
        expect(slot.current).toBe(second)
    })

    test("stale completion cannot clear a newer controller", () => {
        const slot = new AbortControllerSlot()
        const first = slot.replace()
        const second = slot.replace()

        slot.clearIfCurrent(first)

        expect(slot.current).toBe(second)
    })

    test("current completion clears its own controller", () => {
        const slot = new AbortControllerSlot()
        const controller = slot.replace()

        slot.clearIfCurrent(controller)

        expect(slot.current).toBeNull()
    })

    test("teardown aborts and clears the live controller", () => {
        const slot = new AbortControllerSlot()
        const controller = slot.replace()

        slot.abort()

        expect(controller.signal.aborted).toBe(true)
        expect(slot.current).toBeNull()
    })
})
