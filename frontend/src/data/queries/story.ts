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
} from "../../infrastructure/api/types"
import { chapterKeys } from "./chapter"
import { unwrapResultAsync } from "../../shared/types"

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
}

// ─── Queries ───────────────────────────────────────────────────────────────

export function useStories() {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.list(),
        queryFn: ({ signal }) => unwrapResultAsync(api.story.getStories(requestOptions({ signal }))),
    })
}

export function useStoryDetails(storyId: string) {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.detail(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.getStoryDetails(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
}

export function useStoryChapters(storyId: string) {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.chapters(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.getStoryChapters(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
    })
}

export function useStoryTags(storyId: string) {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.tags(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.listStoryTags(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
        // Vocabulary changes only when scenes are re-extracted; tolerate
        // a 5-minute stale window before background refetch.
        staleTime: 5 * 60 * 1000,
    })
}

export function useStoryEntities(storyId: string) {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.entities(storyId),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.listStoryEntities(storyId, requestOptions({ signal }))),
        enabled: Boolean(storyId),
        staleTime: 5 * 60 * 1000,
    })
}

/**
 * Hybrid scene search. Idempotent / read-shaped despite being POST, so it
 * lives in the query layer (cacheable, abortable). Empty query string
 * disables the request so a mounted-but-empty search panel doesn't fire
 * a no-op call.
 *
 * `placeholderData: keepPreviousData` keeps the previous result visible
 * while a new filter combination is in flight — avoids the result list
 * blanking on every keystroke / tag toggle.
 */
export function useStorySceneSearch(
    storyId: string,
    request: SceneSearchRequest,
) {
    const api = useApi()
    return useQuery({
        queryKey: storyKeys.sceneSearch(storyId, request),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.story.searchStoryScenes(storyId, request, requestOptions({ signal }))),
        enabled: Boolean(storyId) && request.query.trim().length > 0,
        placeholderData: keepPreviousData,
        staleTime: 60 * 1000,
    })
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
        },
    })
}

export function useUpdateStory() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateStoryRequest) =>
            unwrapResultAsync(api.story.updateStory(payload)),
        // Title / metadata change — list cards reflect it, detail too.
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.all })
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
            // New chapter affects story detail (chapter list).
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
        },
    })
}

export function useReorderChapters(storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: ReorderChapterRequest) =>
            unwrapResultAsync(api.story.reorderChapters(storyId, payload)),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
            // Per-chapter prev/next pointers shift on reorder.
            qc.invalidateQueries({ queryKey: chapterKeys.all })
        },
    })
}