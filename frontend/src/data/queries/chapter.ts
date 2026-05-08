import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type UpdateChapterRequest,
    requestOptions,
} from "../../infrastructure/api/types"
import { storyKeys } from "./story"
import { unwrapResultAsync } from "../../shared/types"

// ─── Keys ──────────────────────────────────────────────────────────────────
// Chapter cache lives under its own root because chapters are also
// fetched in isolation by chapter_id (e.g. deep links). Mutations also
// hit storyKeys to keep the parent's chapter list consistent.

export const chapterKeys = {
    all: ["chapters"] as const,
    detail: (chapterId: string, asHtml: boolean) =>
        [...chapterKeys.all, "detail", chapterId, { asHtml }] as const,
}

// ─── Queries ───────────────────────────────────────────────────────────────

export function useChapter(chapterId: string, asHtml: boolean = true) {
    const api = useApi()
    return useQuery({
        queryKey: chapterKeys.detail(chapterId, asHtml),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.chapter.getChapter(chapterId, asHtml, requestOptions({ signal }))),
        enabled: Boolean(chapterId),
    })
}

// ─── Mutations ─────────────────────────────────────────────────────────────

export function useUpdateChapter(chapterId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateChapterRequest) =>
            unwrapResultAsync(api.chapter.updateChapter(chapterId, payload)),
        onSuccess: (chapter) => {
            // Wipe cached detail entries for this chapter (both html
            // representations).
            qc.invalidateQueries({
                queryKey: [...chapterKeys.all, "detail", chapterId],
            })
            // Title / order may have changed — parent story view shows
            // them in its chapter list.
            qc.invalidateQueries({
                queryKey: storyKeys.detail(chapter.storyId),
            })
        },
    })
}

export function useDeleteChapter(chapterId: string, storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: () => unwrapResultAsync(api.chapter.deleteChapter(chapterId)),
        onSuccess: () => {
            qc.removeQueries({
                queryKey: [...chapterKeys.all, "detail", chapterId],
            })
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
        },
    })
}