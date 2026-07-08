import { useState } from "react";
import type { AsyncState, ChapterListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { ChapterEditorSidebarProps } from "./ChapterEditorSidebar";


export type UseChapterEditorSidebarProps = 
{
    state: AsyncState<ChapterListResponse, ApiError>
    selectedChapterId: string
    onSelectChapter: (chapterId: string) => void
}


export function useChapterEditorSidebarProps({
    state,
    selectedChapterId,
    onSelectChapter
}: UseChapterEditorSidebarProps): ChapterEditorSidebarProps {

    const [sidebarOpen, setSidebarOpen] = useState(true)

    switch (state.status) {
        case "idle":
        case "loading": {
            return {
                status: "loading",
                open: sidebarOpen,
                onOpenChange: (prev: boolean) => setSidebarOpen(!prev)
            }
        }
        case "error": {
            return { status: "error" } 
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
                items: data.chapters.map((chapter) => {
                    if (chapter.chapterId === selectedChapterId) 
                        return {
                            status: "selected",
                            chapterId: chapter.chapterId,
                            storyId: chapter.storyId,
                            chapterTitle: chapter.chapterTitle,
                            chapterNumber: chapter.chapterNumber,
                            chapterStatus: chapter.published ? "published" : "draft",
                            onClick: () => onSelectChapter(chapter.chapterId)
                        }
                    else
                        return {
                            status: "idle",
                            chapterId: chapter.chapterId,
                            storyId: chapter.storyId,
                            chapterTitle: chapter.chapterTitle,
                            chapterStatus: chapter.published ? "published" : "draft",
                            chapterNumber: chapter.chapterNumber,
                            onClick: () => onSelectChapter(chapter.chapterId)
                        }
                })
            }
        }
    }
}