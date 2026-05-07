import {
    useQuery,
    useMutation,
    useQueryClient,
    keepPreviousData,
} from "@tanstack/react-query"
import { api } from "../../infrastructure/api"
import type {
    CreateStoryRequest,
    UpdateStoryRequest,
    CreateChapterRequest,
    ReorderChapterRequest,
    SceneSearchRequest,
} from "../../infrastructure/api/types"
import { chapterKeys } from "./chapter"

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
    return useQuery({
        queryKey: storyKeys.list(),
        queryFn: ({ signal }) => api.story.getStories({ signal }),
    })
}

export function useStoryDetails(storyId: string) {
    return useQuery({
        queryKey: storyKeys.detail(storyId),
        queryFn: ({ signal }) =>
            api.story.getStoryDetails(storyId, { signal }),
        enabled: Boolean(storyId),
    })
}

export function useStoryChapters(storyId: string) {
    return useQuery({
        queryKey: storyKeys.chapters(storyId),
        queryFn: ({ signal }) =>
            api.story.getStoryChapters(storyId, { signal }),
        enabled: Boolean(storyId),
    })
}

export function useStoryTags(storyId: string) {
    return useQuery({
        queryKey: storyKeys.tags(storyId),
        queryFn: ({ signal }) =>
            api.story.listStoryTags(storyId, { signal }),
        enabled: Boolean(storyId),
        // Vocabulary changes only when scenes are re-extracted; tolerate
        // a 5-minute stale window before background refetch.
        staleTime: 5 * 60 * 1000,
    })
}

export function useStoryEntities(storyId: string) {
    return useQuery({
        queryKey: storyKeys.entities(storyId),
        queryFn: ({ signal }) =>
            api.story.listStoryEntities(storyId, { signal }),
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
    return useQuery({
        queryKey: storyKeys.sceneSearch(storyId, request),
        queryFn: ({ signal }) =>
            api.story.searchStoryScenes(storyId, request, { signal }),
        enabled: Boolean(storyId) && request.query.trim().length > 0,
        placeholderData: keepPreviousData,
        staleTime: 60 * 1000,
    })
}

// ─── Mutations ─────────────────────────────────────────────────────────────

export function useCreateStory() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateStoryRequest) =>
            api.story.createStory(payload),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.list() })
        },
    })
}

export function useUpdateStory() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateStoryRequest) =>
            api.story.updateStory(payload),
        // Title / metadata change — list cards reflect it, detail too.
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.all })
        },
    })
}

export function useDeleteStory() {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (storyId: string) => api.story.deleteStory(storyId),
        onSuccess: (_data, storyId) => {
            qc.removeQueries({ queryKey: storyKeys.detail(storyId) })
            qc.invalidateQueries({ queryKey: storyKeys.list() })
        },
    })
}

export function useCreateChapter(storyId: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: CreateChapterRequest) =>
            api.story.createChapter(storyId, payload),
        onSuccess: () => {
            // New chapter affects story detail (chapter list).
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
        },
    })
}

export function useReorderChapters(storyId: string) {
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: ReorderChapterRequest) =>
            api.story.reorderChapters(storyId, payload),
        onSuccess: () => {
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
            // Per-chapter prev/next pointers shift on reorder.
            qc.invalidateQueries({ queryKey: chapterKeys.all })
        },
    })
}