import { MutationObserver } from "@tanstack/react-query"
import { describe, expect, test, vi } from "vitest"

import type { AppApi } from "../../src/infrastructure/api"
import { chatKeys, createDeleteThreadMutationOptions } from "../../src/data/queries/chat"
import { ApiError, Err, Ok } from "../../src/shared/types"
import { createIntegrationQueryClient } from "./harness"

function apiWithDelete(deleteThread: AppApi["chat"]["deleteThread"]): AppApi {
    return {
        chat: { deleteThread } as AppApi["chat"],
    } as AppApi
}

describe("thread deletion integration", () => {
    test("a failed deletion leaves cached messages and navigation untouched", async () => {
        const qc = createIntegrationQueryClient()
        const messageKey = chatKeys.messages("story-1", "thread-1")
        const cachedMessages = { messages: [{ id: "message-1" }] }
        qc.setQueryData(messageKey, cachedMessages)

        const failure = new ApiError(500, "Delete failed")
        const deleteThread = vi.fn(async () => Err(failure)) as AppApi["chat"]["deleteThread"]
        const navigate = vi.fn()
        const observer = new MutationObserver(
            qc,
            createDeleteThreadMutationOptions(
                apiWithDelete(deleteThread),
                qc,
                navigate,
                "story-1",
                "thread-1",
            ),
        )

        await expect(observer.mutate(undefined)).rejects.toBe(failure)

        expect(qc.getQueryData(messageKey)).toEqual(cachedMessages)
        expect(navigate).not.toHaveBeenCalled()
    })

    test("a successful deletion removes message cache and navigates only after success", async () => {
        const qc = createIntegrationQueryClient()
        const messageKey = chatKeys.messages("story-1", "thread-1")
        qc.setQueryData(messageKey, { messages: [{ id: "message-1" }] })

        const deleteThread = vi.fn(async () => Ok({} as never)) as AppApi["chat"]["deleteThread"]
        const navigate = vi.fn(async () => undefined)
        const observer = new MutationObserver(
            qc,
            createDeleteThreadMutationOptions(
                apiWithDelete(deleteThread),
                qc,
                navigate,
                "story-1",
                "thread-1",
            ),
        )

        await observer.mutate(undefined)

        expect(qc.getQueryData(messageKey)).toBeUndefined()
        expect(navigate).toHaveBeenCalledOnce()
        expect(navigate).toHaveBeenCalledWith({
            to: "/stories/$storyId/chat/new",
            params: { storyId: "story-1" },
        })
    })
})
