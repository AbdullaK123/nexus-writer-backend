import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type ChapterContentResponse,
    type ChapterSummaryResponse,
    type UpdateChapterRequest,
    requestOptions,
} from "../../infrastructure/api/types"
import { storyKeys } from "./story"
import { ApiError, unwrapResultAsync } from "../../shared/types"
import { toAsyncState } from "../../infrastructure/api/utils";
import { Option } from "oxide.ts"
import { authKeys } from "./auth";

// ─── Keys ──────────────────────────────────────────────────────────────────
// Chapter cache lives under its own root because chapters are also
// fetched in isolation by chapter_id (e.g. deep links). Mutations also
// hit storyKeys to keep the parent's chapter list consistent.

export const chapterKeys = {
    all: ["chapters"] as const,
    detail: (chapterId: string, asHtml: boolean) =>
        [...chapterKeys.all, "detail", chapterId, { asHtml }] as const,
    summary: (chapterId: string) => 
        [...chapterKeys.all, chapterId, "summary"]
}

// ─── Queries ───────────────────────────────────────────────────────────────

export function useChapter(chapterId: string, asHtml: boolean = true) {
    const api = useApi()
    const result = useQuery<ChapterContentResponse, ApiError>({
        queryKey: chapterKeys.detail(chapterId, asHtml),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.chapter.getChapter(chapterId, asHtml, requestOptions({ signal }))),
        enabled: Boolean(chapterId),
    })
    return [toAsyncState<ChapterContentResponse>(result), result.refetch] as const
}

// ─── Mutations ─────────────────────────────────────────────────────────────

export function useUpdateChapter(chapterId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateChapterRequest) =>
            unwrapResultAsync(api.chapter.updateChapter(chapterId, payload)),
        onMutate: async (updatedContent) => {
            await qc.cancelQueries({ queryKey: chapterKeys.detail(chapterId, true) })
            const prevContent = qc.getQueryData<ChapterContentResponse>(chapterKeys.detail(chapterId, true))
             qc.setQueryData<ChapterContentResponse>(
                chapterKeys.detail(chapterId, true), 
                {
                    // Provide hardcoded or empty fallbacks for required fields
                    id: prevContent?.id ?? chapterId,
                    title: prevContent?.title ?? "",
                    published: prevContent?.published ?? false,
                    storyId: prevContent?.storyId ?? "",
                    storyTitle: prevContent?.storyTitle ?? "",
                    chapterNumber: prevContent?.chapterNumber ?? 0,
                    wordCount: prevContent?.wordCount ?? 0,
                    createdAt: prevContent?.createdAt ?? new Date(),
                    updatedAt: prevContent?.updatedAt ?? new Date(),
                    previousChapterId: prevContent?.previousChapterId ?? null,
                    nextChapterId: prevContent?.nextChapterId ?? null,
                    // Your dynamic update
                    content: updatedContent.content ?? ""
                }
            )
            return {
                prevContent,
                updatedContent
            }
        },
        onError: (_, __, context ) => {
            qc.setQueryData(chapterKeys.detail(chapterId, true), context?.prevContent)
        },
        onSuccess: (chapter) => {
            qc.invalidateQueries({
                queryKey: [...chapterKeys.all, "detail", chapterId],
            })
            qc.invalidateQueries({
                queryKey: storyKeys.detail(chapter.storyId),
            })
            qc.invalidateQueries({
                queryKey: authKeys.dashboard()
            })
        },
        onSettled: (_) => {
            qc.invalidateQueries({ queryKey: chapterKeys.detail(chapterId, true) })
        }
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
            qc.invalidateQueries({
                queryKey: authKeys.dashboard()
            })
        },
    })
}

export function useChapterSummary(chapterId: Option<string>) {
   

  const api = useApi()

  const enabled = chapterId.isSome()
  const id = chapterId.unwrapOr("__none__")

  const result = useQuery<ChapterSummaryResponse, ApiError>({
    queryKey: chapterKeys.summary(id),
    queryFn: ({ signal }) =>
      unwrapResultAsync(
        api.chapter.summarizeChapter(id, requestOptions({ signal }))
      ),
    enabled,
    staleTime: 1000*10
  })

  return [toAsyncState<ChapterSummaryResponse>(result), result.refetch] as const
}