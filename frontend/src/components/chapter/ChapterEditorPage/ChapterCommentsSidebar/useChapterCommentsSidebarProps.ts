import { useEffect, useMemo, useState } from "react";
import type { AsyncState, CommentCategory, CommentExtractionResponse, ExtractedComment } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { ChapterCommentsSidebarProps } from "./ChapterCommentsSidebar";
import type { FilterCounts } from "./ChapterCommentsSidebarHeader";
import { useNavigate } from "@tanstack/react-router";
import { useCreateThread } from "../../../../data/queries";
import { useToast } from "../../../common";




export type UseChapterCommentsSidebarPropsArgs = 
{
    storyId: string,
    state: AsyncState<CommentExtractionResponse, ApiError>,
}

export type CommentView = "active" | "dismissed"
export type DismissedComment = {
    issueKey: string
    category: CommentCategory
}

export function useChapterCommentsSidebarProps({
    storyId,
    state,
}: UseChapterCommentsSidebarPropsArgs): ChapterCommentsSidebarProps {

    const [sidebarOpen, setSidebarOpen] = useState(false)
    const [activeCategory, setActiveCategory] = useState<CommentCategory | "all">("all")
    const {
        mutate: createThread
    } = useCreateThread(storyId)
    const navigate = useNavigate()
    const { error } = useToast()

    const [commentView, setCommentView] = useState<CommentView>("active")
    const [dismissedKeys, setDismissedKeys] = useState<DismissedComment[]>([])


    const dismissComment = (issueKey: string, category: CommentCategory) => {
        setDismissedKeys((prev) => 
            prev.map((comment) => comment.issueKey).includes(issueKey)
            ? prev
            : [...prev, { issueKey: issueKey, category: category }]
        )
    }

    const restoreComment = (issueKey: string) => {
        setDismissedKeys((prev) => 
            prev.filter((comment) => comment.issueKey !== issueKey)
        )
    }


    const onDigIntoThis = (
        comment: ExtractedComment, 
        chapterNumber: number,
        onThreadCreationPendingChange: (e: boolean) => void
    ) => {
        
        const evidence = []

        if (comment.evidence.length > 0) {
            evidence.push("## Evidence cited:")
            evidence.push("")
            comment.evidence.forEach((ev) => {
                evidence.push("### Quoted text:")
                evidence.push("")
                evidence.push(`> ${ev.quoted_text}`)
                evidence.push("")
                evidence.push("### Relevance:")
                evidence.push("")
                evidence.push(ev.relevance)
            })
        }

        const message = [
            `The comments system flagged this passage in Chapter ${chapterNumber}`,
            "",
            `> ${comment.quoted_text}`,
            "",
            `Concern: ${comment.title}`,
            "",
            `Category: ${comment.category}`,
            "",
            `Scope: ${comment.scope}`,
            "",
            `Priority: ${comment.priority}`,
            "",
            comment.body,
            "",
            evidence.join("\n"),
            "",
            "Verify this against the manuscript. Is this a real issue? Show me the relevant scenes and explain what you find."
        ].join("\n")

        onThreadCreationPendingChange(true)

        createThread(
            {
                firstMessage: message
            },
            {
                onSuccess: async (newThread) => {
                    onThreadCreationPendingChange(false)
                    await navigate({
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                        storyId: storyId,
                        threadId: newThread.threadId
                        },
                        search: {
                        prompt: message
                        }
                    })
                },
                onError: () => {
                    onThreadCreationPendingChange(false)
                    error("Error", "Something went wrong and we could not investigate your pulse finding. The server might be experiencing issues.")
                }
            }
        )
    }

    const commentBatchKey = useMemo(() => {
        if (state.status === "success") {

            const data = state.data.unwrap().unwrap()

            return `${data.chapterId}:${data.generatedAt.toISOString()}`
        }
    }, [state])

    useEffect(() => {
        if (commentBatchKey) {
            requestAnimationFrame(() => {
                setCommentView("active")
                setDismissedKeys([])
            })
        }
    }, [commentBatchKey])


    switch (state.status) {
        case "idle": {
            return { status: "idle"}
        }
        case "empty": {
            return { status: "empty" }
        }
        case "loading": {
            return { status: "loading" }
        }
        case "success": {

            const data = state.data.unwrap().unwrap()

            const filterCounts = data.extraction.comments.reduce((acc, item) => {
                const key = item.category as string
                acc[key] = (acc[key] || 0) + 1
                return acc
            }, {} as Record<string, number> )

            filterCounts['all'] = data.extraction.comments.length

            return {
                status: "ready",
                header: {
                    activeCategory: activeCategory,
                    filterCounts: filterCounts as FilterCounts,
                    sidebarOpen: sidebarOpen,
                    dismissedKeys: dismissedKeys,
                    view: commentView,
                    onViewChange: (view: CommentView) => setCommentView(view),
                    onSidebarOpenChange: (e: boolean) => setSidebarOpen(!e),
                    onClickAll: () => setActiveCategory("all"),
                    onClickCharacter: () => setActiveCategory("character"),
                    onClickContinuity: () => setActiveCategory("continuity"),
                    onClickClarity: () => setActiveCategory("clarity"),
                    onClickPlot: () => setActiveCategory("plot"),
                    onClickStructure: () => setActiveCategory("structure"),
                    onClickPacing: () => setActiveCategory("pacing"),
                    onClickDialogue: () => setActiveCategory("dialogue"),
                    onClickProse: () => setActiveCategory("prose"),
                    onClickWorld: () => setActiveCategory("worldbuilding")
                },
                comments: data.extraction.comments.map((comment) => ({
                    chapterNumber: data.chapterNumber,
                    comment: comment,
                    view: dismissedKeys.map((comment) => comment.issueKey).includes(comment.issue_key) ? "dismissed" : "active",
                    onDismiss: () => dismissComment(comment.issue_key, comment.category),
                    onRestore: () => restoreComment(comment.issue_key),
                    onDigIntoThis: onDigIntoThis
                }))
            }


        }

    }

}