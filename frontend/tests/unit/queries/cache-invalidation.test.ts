import { beforeEach, describe, expect, test, vi } from "vitest"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useNavigate } from "@tanstack/react-router"

import { useApi } from "../../../src/data/providers/ApiProvider"
import { authKeys, useLogout } from "../../../src/data/queries/auth"
import {
    chatKeys,
    useCreateThread,
    useDeleteThread,
    useRenameThread,
} from "../../../src/data/queries/chat"
import {
    storyKeys,
    useCreateChapter,
    useCreateStory,
    useDeleteStory,
    useReorderChapters,
} from "../../../src/data/queries/story"
import { chapterKeys } from "../../../src/data/queries/chapter"

vi.mock("@tanstack/react-query", () => ({
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
    keepPreviousData: Symbol("keepPreviousData"),
}))

vi.mock("@tanstack/react-router", () => ({
    useNavigate: vi.fn(),
}))

vi.mock("../../../src/data/providers/ApiProvider", () => ({
    useApi: vi.fn(),
}))

const invalidateQueries = vi.fn()
const removeQueries = vi.fn()
const clear = vi.fn()
const navigate = vi.fn()

function mutationOptions() {
    return vi.mocked(useMutation).mock.calls.at(-1)?.[0] as {
        onSuccess?: (...args: never[]) => unknown
    }
}

beforeEach(() => {
    invalidateQueries.mockReset()
    removeQueries.mockReset()
    clear.mockReset()
    navigate.mockReset()
    vi.mocked(useMutation).mockReset()

    vi.mocked(useQueryClient).mockReturnValue({
        invalidateQueries,
        removeQueries,
        clear,
    } as never)
    vi.mocked(useNavigate).mockReturnValue(navigate as never)
    vi.mocked(useApi).mockReturnValue({
        auth: { logout: vi.fn() },
        chat: {
            createThread: vi.fn(),
            renameThread: vi.fn(),
            deleteThread: vi.fn(),
        },
        story: {
            createStory: vi.fn(),
            createChapter: vi.fn(),
            deleteStory: vi.fn(),
            reorderChapters: vi.fn(),
        },
    } as never)
})

describe("query cache invalidation", () => {
    test("creating a story refreshes story cards and dashboard", () => {
        useCreateStory()
        mutationOptions().onSuccess?.()

        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: storyKeys.list() })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: authKeys.dashboard() })
    })

    test("creating a chapter refreshes every story/chapter navigation surface", () => {
        useCreateChapter("story-1")
        mutationOptions().onSuccess?.()

        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: storyKeys.detail("story-1") })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: storyKeys.chapters("story-1") })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: storyKeys.path("story-1") })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: chapterKeys.all })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: authKeys.dashboard() })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: authKeys.editorLinks() })
    })

    test("reordering chapters preserves optimistic ordering while refreshing dependent navigation", () => {
        useReorderChapters("story-1")
        mutationOptions().onSuccess?.()

        expect(invalidateQueries).toHaveBeenCalledWith({
            queryKey: storyKeys.detail("story-1"),
            exact: true,
        })
        expect(invalidateQueries).not.toHaveBeenCalledWith({ queryKey: storyKeys.chapters("story-1") })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: storyKeys.path("story-1") })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: chapterKeys.all })
    })

    test("creating or renaming a thread refreshes the story thread list", () => {
        useCreateThread("story-1")
        mutationOptions().onSuccess?.()
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: chatKeys.threads("story-1") })

        invalidateQueries.mockClear()
        useRenameThread("story-1", "thread-1")
        mutationOptions().onSuccess?.()
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: chatKeys.threads("story-1") })
    })

    test("destructive mutations have no cache/navigation side effects before success", () => {
        useDeleteThread("story-1", "thread-1")
        useDeleteStory()

        expect(removeQueries).not.toHaveBeenCalled()
        expect(invalidateQueries).not.toHaveBeenCalled()
        expect(navigate).not.toHaveBeenCalled()
    })

    test("deleting a thread removes its message cache before refreshing threads", async () => {
        useDeleteThread("story-1", "thread-1")
        await mutationOptions().onSuccess?.()

        expect(removeQueries).toHaveBeenCalledWith({
            queryKey: chatKeys.messages("story-1", "thread-1"),
        })
        expect(invalidateQueries).toHaveBeenCalledWith({ queryKey: chatKeys.threads("story-1") })
        expect(navigate).toHaveBeenCalledWith({
            to: "/stories/$storyId/chat/new",
            params: { storyId: "story-1" },
        })
    })

    test("logout clears all user-scoped cached data", () => {
        useLogout()
        mutationOptions().onSuccess?.()

        expect(clear).toHaveBeenCalledOnce()
    })
})
