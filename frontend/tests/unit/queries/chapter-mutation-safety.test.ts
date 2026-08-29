import { beforeEach, describe, expect, test, vi } from "vitest"
import { useMutation, useQueryClient } from "@tanstack/react-query"
import { useMatchRoute, useNavigate } from "@tanstack/react-router"

import { useApi } from "../../../src/data/providers/ApiProvider"
import {
    chapterKeys,
    useDeleteChapter,
    useUpdateChapter,
} from "../../../src/data/queries/chapter"

vi.mock("@tanstack/react-query", () => ({
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
}))

vi.mock("@tanstack/react-router", () => ({
    useNavigate: vi.fn(),
    useMatchRoute: vi.fn(),
}))

vi.mock("../../../src/data/providers/ApiProvider", () => ({
    useApi: vi.fn(),
}))

const cancelQueries = vi.fn()
const getQueryData = vi.fn()
const setQueryData = vi.fn()
const fetchQuery = vi.fn()
const invalidateQueries = vi.fn()
const removeQueries = vi.fn()
const navigate = vi.fn()
const matchRoute = vi.fn()

function mutationOptions() {
    return vi.mocked(useMutation).mock.calls.at(-1)?.[0] as {
        onMutate?: (variables: any) => any
        onError?: (error: unknown, variables: any, context: any) => any
        onSuccess?: (data: any, variables?: any, context?: any) => any
    }
}

const cachedChapter = {
    id: "chapter-1",
    title: "Old title",
    published: false,
    content: "<p>keep me</p>",
    storyId: "story-1",
    storyTitle: "Story",
    chapterNumber: 1,
    wordCount: 2,
    createdAt: new Date("2026-01-01T00:00:00Z"),
    updatedAt: new Date("2026-01-01T00:00:00Z"),
    previousChapterId: null,
    nextChapterId: "chapter-2",
}

beforeEach(() => {
    vi.mocked(useMutation).mockReset()
    cancelQueries.mockReset()
    getQueryData.mockReset()
    setQueryData.mockReset()
    fetchQuery.mockReset()
    invalidateQueries.mockReset()
    removeQueries.mockReset()
    navigate.mockReset()
    matchRoute.mockReset()

    vi.mocked(useQueryClient).mockReturnValue({
        cancelQueries,
        getQueryData,
        setQueryData,
        fetchQuery,
        invalidateQueries,
        removeQueries,
    } as never)
    vi.mocked(useNavigate).mockReturnValue(navigate as never)
    vi.mocked(useMatchRoute).mockReturnValue(matchRoute as never)
    vi.mocked(useApi).mockReturnValue({
        chapter: {
            updateChapter: vi.fn(),
            deleteChapter: vi.fn(),
        },
        story: { getPathArray: vi.fn() },
    } as never)
})

describe("chapter mutation safety", () => {
    test("title-only optimistic update preserves cached content", async () => {
        getQueryData.mockReturnValue(cachedChapter)
        useUpdateChapter("chapter-1")

        await mutationOptions().onMutate?.({ title: "New title" })

        expect(setQueryData).toHaveBeenCalledWith(
            chapterKeys.detail("chapter-1", true),
            expect.objectContaining({
                title: "New title",
                content: "<p>keep me</p>",
            }),
        )
    })

    test("failed optimistic update restores the previous cached chapter", async () => {
        getQueryData.mockReturnValue(cachedChapter)
        useUpdateChapter("chapter-1")
        const options = mutationOptions()
        const context = await options.onMutate?.({ content: "<p>new</p>" })

        options.onError?.(new Error("boom"), { content: "<p>new</p>" }, context)

        expect(setQueryData).toHaveBeenLastCalledWith(
            chapterKeys.detail("chapter-1", true),
            cachedChapter,
        )
    })

    test("delete does not navigate away before the server confirms success", async () => {
        matchRoute.mockReturnValue(true)
        fetchQuery.mockResolvedValue({ pathArray: ["chapter-1", "chapter-2"] })
        useDeleteChapter("chapter-1", "story-1")

        await mutationOptions().onMutate?.()

        expect(navigate).not.toHaveBeenCalled()
    })
})
