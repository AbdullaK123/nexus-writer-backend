import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type ChapterContentResponse,
    type ChapterSummaryResponse,
    type CommentExtractionResponse,
    type UpdateChapterRequest,
    requestOptions,
} from "../../infrastructure/api/types"
import { storyKeys } from "./story"
import { ApiError, unwrapResultAsync } from "../../shared/types"
import { toAsyncState } from "../../infrastructure/api/utils";
import { Option } from "oxide.ts"
import { authKeys } from "./auth";
import { useMatchRoute, useNavigate } from "@tanstack/react-router";

export const chapterKeys = {
    all: ["chapters"] as const,
    detail: (chapterId: string, asHtml: boolean) =>
        [...chapterKeys.all, "detail", chapterId, { asHtml }] as const,
    summary: (chapterId: string) => 
        [...chapterKeys.all, chapterId, "summary"],
    comments: (chapterId: string) =>
        [...chapterKeys.all, chapterId, "comments"]
}

export function useChapter(chapterId: string, asHtml: boolean = true) {
    const api = useApi()
    const result = useQuery<ChapterContentResponse, ApiError>({
        queryKey: chapterKeys.detail(chapterId, asHtml),
        queryFn: ({ signal }) =>
            unwrapResultAsync(api.chapter.getChapter(chapterId, asHtml, requestOptions({ signal }))),
        enabled: Boolean(chapterId),
    })
    return toAsyncState<ChapterContentResponse>(result)
}

export function useUpdateChapter(chapterId: string) {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation({
        mutationFn: (payload: UpdateChapterRequest) =>
            unwrapResultAsync(api.chapter.updateChapter(chapterId, payload)),
        onMutate: async (updatedContent) => {
            const key = chapterKeys.detail(chapterId, true)
            await qc.cancelQueries({ queryKey: key })
            const prevContent = qc.getQueryData<ChapterContentResponse>(key)

            const optimisticContent: ChapterContentResponse = prevContent
                ? { ...prevContent, ...updatedContent }
                : {
                    id: chapterId,
                    title: updatedContent.title ?? "",
                    published: updatedContent.published ?? false,
                    content: updatedContent.content ?? "",
                    storyId: "",
                    storyTitle: "",
                    chapterNumber: 0,
                    wordCount: 0,
                    createdAt: new Date(),
                    updatedAt: new Date(),
                    previousChapterId: null,
                    nextChapterId: null,
                }

            qc.setQueryData<ChapterContentResponse>(key, optimisticContent)
            return { prevContent }
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
            qc.invalidateQueries({ queryKey: authKeys.dashboard() })
        },
        onSettled: () => {
            qc.invalidateQueries({ queryKey: chapterKeys.detail(chapterId, true) })
        }
    })
}

type DeleteChapterContext = {
    destination?:
        | { to: "/stories/$storyId"; params: { storyId: string } }
        | { to: "/stories/$storyId/$chapterId"; params: { storyId: string; chapterId: string } }
}

export function useDeleteChapter(chapterId: string, storyId: string) {
    const api = useApi()
    const qc = useQueryClient()
    const navigate = useNavigate()
    const matchRoute = useMatchRoute()

    return useMutation({
        onMutate: async (): Promise<DeleteChapterContext> => {
            const isViewingChapter = matchRoute({ 
                to: "/stories/$storyId/$chapterId", 
                params: { storyId, chapterId } 
            })
            if (!isViewingChapter) return {}

            const pathKey = storyKeys.path(storyId)
            await qc.cancelQueries({ queryKey: pathKey })
            const pathArray = await qc.fetchQuery({
                queryKey: pathKey,
                queryFn: () => unwrapResultAsync(api.story.getPathArray(storyId))
            })
            const chapterIdx = pathArray.pathArray.findIndex((id) => id === chapterId)
            if (chapterIdx === -1) return {}

            if (chapterIdx === 0) {
                return {
                    destination: {
                        to: "/stories/$storyId",
                        params: { storyId },
                    }
                }
            }

            const prevChapterId = pathArray.pathArray[chapterIdx - 1]
            if (!prevChapterId) return {}
            return {
                destination: {
                    to: "/stories/$storyId/$chapterId",
                    params: { storyId, chapterId: prevChapterId },
                }
            }
        },
        mutationFn: () => unwrapResultAsync(api.chapter.deleteChapter(chapterId)),
        onSuccess: async (_data, _variables, context) => {
            if (context?.destination) {
                await navigate(context.destination)
            }
            qc.removeQueries({
                queryKey: [...chapterKeys.all, "detail", chapterId],
            })
            qc.invalidateQueries({ queryKey: chapterKeys.all })
            qc.invalidateQueries({ queryKey: storyKeys.chapters(storyId) })
            qc.invalidateQueries({ queryKey: storyKeys.path(storyId) })
            qc.invalidateQueries({ queryKey: storyKeys.detail(storyId) })
            qc.invalidateQueries({ queryKey: authKeys.dashboard() })
            qc.invalidateQueries({ queryKey: authKeys.editorLinks()})
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
      unwrapResultAsync(api.chapter.summarizeChapter(id, requestOptions({ signal }))),
    enabled,
    staleTime: 1000*10
  })
  return toAsyncState<ChapterSummaryResponse>(result)
}

export function useChapterComments(chapterId: string) {
    const api = useApi()
    const result = useQuery<CommentExtractionResponse, ApiError>({
        queryKey: chapterKeys.comments(chapterId),
        queryFn: ({ signal }) => 
            unwrapResultAsync(api.chapter.getComments(chapterId, requestOptions({ signal }))),
        enabled: Boolean(chapterId),
        staleTime: 1000*10
    })
    return toAsyncState<CommentExtractionResponse>(result)
}
