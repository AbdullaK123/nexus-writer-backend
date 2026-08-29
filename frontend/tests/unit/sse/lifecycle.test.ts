import { describe, expect, test, vi } from "vitest"

import { createSseLifecycleCleanup } from "../../../src/infrastructure/sse/lifecycle"
import { AbortControllerSlot } from "../../../src/shared/abortControllerSlot"

describe("SSE lifecycle cleanup", () => {
    test("auth teardown aborts the live stream and clears reconnect timer", () => {
        const slot = new AbortControllerSlot()
        const controller = slot.replace()
        const timerRef = { current: 42 as number | null }
        const stoppedRef = { current: false }
        const clearTimer = vi.fn()

        const cleanup = createSseLifecycleCleanup(
            slot,
            timerRef,
            stoppedRef,
            clearTimer,
        )
        cleanup()

        expect(controller.signal.aborted).toBe(true)
        expect(slot.current).toBeNull()
        expect(stoppedRef.current).toBe(true)
        expect(clearTimer).toHaveBeenCalledWith(42)
        expect(timerRef.current).toBeNull()
    })
})
