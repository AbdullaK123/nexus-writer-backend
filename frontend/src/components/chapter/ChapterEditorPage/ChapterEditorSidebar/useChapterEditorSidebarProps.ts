import { useState } from "react";
import type { AsyncState, ChapterListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useReorderChapters } from "../../../../data/queries";
import { useToast } from "../../../common";
import { buildReorderRequest } from "./reorder";


export type UseChapterEditorSidebarProps = 
{
    storyId: string
    state: AsyncState<ChapterListResponse, ApiError>
    selectedChapterId: string
    onSelectChapter: (chapterId: string) => void
}


export function useChapterEditorSidebarProps({
    storyId,
    state,
    selectedChapterId,
    onSelectChapter
}: UseChapterEditorSidebarProps): ChapterEditorSidebarProps {

    const [sidebarOpen, setSidebarOpen] = useState(true)

    const { error, success } = useToast()

    const {
        mutate: reorderChapters,
        isPending: reorderPending,
    } = useReorderChapters(storyId)

    const itemCount = state.status === "success"
        ? state.data.unwrap().unwrap().chapters.length
        : 0

    const onReorderChapters = (fromPos: number, toPos: number) => {
        if (reorderPending) return

        const payload = buildReorderRequest(fromPos, toPos, itemCount)
        if (!payload) return

        reorderChapters(
            payload,
            {
                onError: () => {
                    error("Failed to reorder chapters", "Something went wrong. The server might be experiencing issues.")
                },
                onSuccess: () => {
                    success("Successfully reordered chapters!", "")
                }
            }
        )
    }

    switch (state.status) {
        case "idle":
        case "loading": {
            return {
                status: "loading"
            }
        }
        case "empty": {
            return { status: "empty" }
        }
        case "success": {
            
            const data = state.data.unwrap().unwrap()

            return {
                status: "ready",
                open: sidebarOpen,
                onOpenChange: (prev: boolean) => setSidebarOpen(!prev),
                storyId: data.storyId,
                storyTitle: data.storyTitle,
                onReorder: onReorderChapters,
                items: data.chapters.map((chapter, idx) => {
                    if (chapter.chapterId === selectedChapterId) 
                        return {
                            status: "selected",
                            index: idx,
                            chapterId: chapter.chapterId,
                            storyId: chapter.storyId,
                            chapterTitle: chapter.chapterTitle,
                            chapterNumber: chapter.chapterNumber,
                            chapterStatus: chapter.published ? "published" : "draft",
                            reorderDisabled: reorderPending,
                            onClick: () => onSelectChapter(chapter.chapterId)
                        }
                    else
                        return {
                            status: "idle",
                            index: idx,
                            chapterId: chapter.chapterId,
                            storyId: chapter.storyId,
                            chapterTitle: chapter.chapterTitle,
                            chapterStatus: chapter.published ? "published" : "draft",
                            chapterNumber: chapter.chapterNumber,
                            reorderDisabled: reorderPending,
                            onClick: () => onSelectChapter(chapter.chapterId)
                        }
                })
            }
        }
    }
}