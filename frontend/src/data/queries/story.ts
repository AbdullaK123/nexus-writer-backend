import {
    useQuery,
    useMutation,
    useQueryClient,
    keepPreviousData,
} from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type CreateStoryRequest,
    type UpdateStoryRequest,
    type CreateChapterRequest,
    type ReorderChapterRequest,
    type SceneSearchRequest,
    requestOptions,
    type StoryGridResponse,
    type StoryDetailResponse,
    type ChapterListResponse,
    type VocabularyListResponse,
    type SceneSearchListResponse,
    type BookPulseResponse,
    type StoryStatsResponse,
} from "../../infrastructure/api/types"
import { chapterKeys } from "./chapter"
import { ApiError, unwrapResultAsync } from "../../shared/types"
import { toAsyncState } from "../../infrastructure/api/utils";
import { authKeys } from "./auth";

// ─── Keys ──────────────────────────────────────────────────────────────────
// Hierarchy mirrors URL paths so a partial-prefix invalidation cascades
// the way you'd expect: invalidating `detail(id)` also wipes that story's
// chapters / tags / entities / search results.

export const storyKeys = {
    all: ["stories"] as const,
    list: () => [...storyKeys.all, "list"] as const,
    detail: (storyId: string) =>
        [...storyKeys.all, "detail", storyId] as const,
    chapters: (storyId: string) =>
        [...storyKeys.detail(storyId), "chapters"] as const,
    tags: (storyId: string) =>
        [...storyKeys.detail(storyId), "tags"] as const,
    entities: (storyId: string) =>
        [...storyKeys.detail(storyId), "entities"] as const,
    sceneSearch: (storyId: string, request: SceneSearchRequest) =>
        [...storyKeys.detail(storyId), "sceneSearch", request] as const,
    pulse: (storyId: string) =>
        [...storyKeys.detail(storyId), "pulse"],
    stats: (storyId: string) =>
        [...storyKeys.detail(storyId), "stats"],
    path: (storyId: string) => 
        [...storyKeys.detail(storyId), "path"]
}

// ─── Queries ───────────────────────────────────────────────────────────────

export function useStories() {
    const api = useApi()
    const result = useQuery<StoryGridResponse, ApiError>({
        queryKey: storyKeys.list(),
        queryFn: ({ signal }) => unwrapResultAsync<StoryGridResponse, ApiError>(api.story.getStories(requestOptions({ signal }))),
    })
    return toAsyncState<StoryGridResponse>(result)
}

export function useStoryDetails(storyId: string) {
    const api = useApi()
    const result = useQuery<StoryDetailResponse, ApiError>({
        queryKey: storyKeys.detail(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.getStoryDetails(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
    return toAsyncState<StoryDetailResponse>(result)
}

export function useStoryChapters(storyId: string) {
    const api = useApi()
    const result = useQuery<ChapterListResponse, ApiError>({
        queryKey: storyKeys.chapters(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.getStoryChapters(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
    return toAsyncState<ChapterListResponse>(result)
}

export function useStoryTags(storyId: string) {
    const api = useApi()
    return toAsyncState<VocabularyListResponse>(useQuery({
        queryKey: storyKeys.tags(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.listStoryTags(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
        staleTime: 5 * 60 * 1000,
    }))
}

export function useStoryEntities(storyId: string) {
    const api = useApi()
    return toAsyncState<VocabularyListResponse>(useQuery({
        queryKey: storyKeys.entities(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.listStoryEntities(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
        staleTime: 5 * 60 * 1000,
    }))
}

export function useStorySceneSearch(
    storyId: string,
    request: SceneSearchRequest,
) {
    const api = useApi()
    const result = useQuery<SceneSearchListResponse, ApiError>({
        queryKey: storyKeys.sceneSearch(storyId, request),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.searchStoryScenes(storyId, request, requestOptions({ signal }))),
        enabled: Boolean(storyId) && request.query.trim().length > 0,
        placeholderData: keepPreviousData,
        staleTime: 60 * 1000,
    })
    return [toAsyncState<SceneSearchListResponse>(result), result.refetch] as const
}

// ─── Mutations ─────────────────────────────────────────────────────────────

export function useCreateStory() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateStoryRequest) =>
            unwrapResultAsync(api.story.createStory(payload)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.list() })
            qc.invalidateQueries({ queryKey: authKeys.dashboard()})
        },
    })
}

export function useUpdateStory(storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateStoryRequest) =>
            unwrapResultAsync(api.story.updateStory(payload, storyId)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.all })
            qc.invalidateQueries({ queryKey: authKeys.dashboard()})
            qc.invalidateQueries({ queryKey: authKeys.editorLinks()})
        },
    })
}

export function useDeleteStory() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (storyId: string) => unwrapResultAsync(api.story.deleteStory(storyId)),
        onSuccess: (_data, storyId) => {
            qc.removeQueries({ queryKey: storyKeys.detail(storyId) })
            qc.invalidateQueries({ queryKey: storyKeys.list() })
            qc.invalidateQueries({ queryKey: authKeys.dashboard()})
        },
    })
}

export function useCreateChapter(storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateChapterRequest) =>
            unwrapResultAsync(api.story.createChapter(storyId, payload)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
            qc.invalidateQueries({ queryKey: storyKeys.chapters(storyId)})
            qc.invalidateQueries({ queryKey: authKeys.dashboard()})
            qc.invalidateQueries({ queryKey: storyKeys.path(storyId) })
            qc.invalidateQueries({ queryKey: chapterKeys.all})
            qc.invalidateQueries({ queryKey: authKeys.editorLinks()})
        },
    })
}

export function useReorderChapters(storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    const chaptersKey = storyKeys.chapters(storyId)

    return useMutation({
        scope: { id: `story-reorder:${storyId}` },
        mutationFn: (payload: ReorderChapterRequest) =>
            unwrapResultAsync(api.story.reorderChapters(storyId, payload)),
        onMutate: async (payload: ReorderChapterRequest) => {
            await qc.cancelQueries({ queryKey: chaptersKey })
            const previous = qc.getQueryData<ChapterListResponse>(chaptersKey)
            if (!previous) return { previous }

            const chapters = [...previous.chapters]
            const [moved] = chapters.splice(payload.fromPos, 1)
            if (!moved) return { previous }

            chapters.splice(payload.toPos, 0, moved)
            qc.setQueryData<ChapterListResponse>(chaptersKey, {
                ...previous,
                chapters: chapters.map((chapter, index) => ({
                    ...chapter,
                    chapterNumber: index + 1,
                })),
            })

            return { previous }
        },
        onError: (_error, _payload, context) => {
            if (context?.previous) {
                qc.setQueryData(chaptersKey, context.previous)
            }
            qc.invalidateQueries({ queryKey: chaptersKey })
        },
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId), exact: true })
            qc.invalidateQueries({ queryKey: chapterKeys.all })
            qc.invalidateQueries({ queryKey: storyKeys.path(storyId)})
            qc.invalidateQueries({ queryKey: authKeys.dashboard()})
            qc.invalidateQueries({ queryKey: authKeys.editorLinks()})
        },
    })
}

export function useStoryPulse(storyId: string) {
    const api = useApi()
    const result = useQuery<BookPulseResponse, ApiError>({
        queryKey: storyKeys.pulse(storyId),
        queryFn: ({ signal }) => unwrapResultAsync(api.story.getPulse(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
        staleTime: 10*1000
    })
    return toAsyncState<BookPulseResponse>(result)
}

export function useStoryStats(storyId: string) {
    const api = useApi()
    const result = useQuery<StoryStatsResponse, ApiError>({
        queryKey: storyKeys.stats(storyId),
        queryFn: ({ signal }) => unwrapResultAsync(api.story.getStats(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId)
    })
    return toAsyncState<StoryStatsResponse>(result)
}
