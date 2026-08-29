import { AbortControllerSlot } from "../../shared/abortControllerSlot"

type Ref<T> = { current: T }

export function createSseLifecycleCleanup(
    slot: AbortControllerSlot,
    timerRef: Ref<number | null>,
    stoppedRef: Ref<boolean>,
    clearTimer: (id: number) => void,
): () => void {
    return () => {
        stoppedRef.current = true
        slot.abort()
        if (timerRef.current !== null) {
            clearTimer(timerRef.current)
            timerRef.current = null
        }
    }
}
