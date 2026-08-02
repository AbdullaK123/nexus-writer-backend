import { useNavigate, useParams } from "@tanstack/react-router";
import { useChapter, useChapterComments, useCreateThread, useStoryChapters, useUpdateChapter } from "../../../data/queries";
import type { ChapterEditorProps } from "./ChapterEditor";
import { useChapterEditorSidebarProps, type ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useEffect, useEffectEvent, useMemo, useState } from "react";
import { Editor, useEditor } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { debounce } from "lodash"
import { useChapterEditorProps } from "./ChapterEditor"
import { None, Some } from "oxide.ts";
import { useToast } from "../../common";
import type { ChapterCommentsSidebarProps } from "./ChapterCommentsSidebar/ChapterCommentsSidebar";
import { useChapterCommentsSidebarProps } from "./ChapterCommentsSidebar";
export type ChapterEditorPageProps = {
    sidebar: ChapterEditorSidebarProps
    editorProps: ChapterEditorProps
    tipTapEditor: Editor,
    commentsSidebar: ChapterCommentsSidebarProps
}

export function useChapterEditorPage(): ChapterEditorPageProps {

    const params = useParams({ from: "/app/stories/$storyId/$chapterId" })

    const [storyChaptersState, refetchChapterList] = useStoryChapters(params.storyId)
    const [chapterState, refetchChapter] = useChapter(params.chapterId)
    const [commentsState, refetchComments] = useChapterComments(params.chapterId)
    const updateChapterMutation = useUpdateChapter(params.chapterId)
    const [updating, setUpdating] = useState(false)
    const [query, setQuery] = useState("")
    const [threadCreationPending, setThreadCreationPending] = useState(false)
    const {
        mutate: createThread
    } = useCreateThread(params.storyId)
    const navigate = useNavigate()

    const { error } = useToast()

    const onStoryChaptersError = useEffectEvent(() => {
        error("Failed to fetch your chapters", "Somthing went wrong. The server might be experiencing issues.")
    })

    const onChapterError = useEffectEvent(() => {
        error("Failed to load your chapter", "Something went wrong. The server might be experiencing issues.")
    })

    const onCommentsError = useEffectEvent(() => {
        error("Failed to load your comments", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (storyChaptersState.status === "error") onStoryChaptersError()
    }, [storyChaptersState.status])

    useEffect(() => {
        if (chapterState.status === "error") onChapterError()
    }, [chapterState.status])

    useEffect(() => {
        if (commentsState.status === "error") onCommentsError()
    }, [commentsState.status])

    const debouncedUpdate = useMemo(
        () => debounce((htmlContent: string) => {
            setUpdating(true)
            updateChapterMutation.mutate(
                { content: htmlContent },
                {
                    onSettled: () => setUpdating(false)
                }
            );
        }, 500),
        [updateChapterMutation] 
    );
    
    useEffect(() => {
        return () => debouncedUpdate.cancel();
    }, [debouncedUpdate]);

    const editor = useEditor({
        extensions: [StarterKit],
        content: "",
        onUpdate: ({ editor }) => {
            const html = editor.getHTML()
            debouncedUpdate(html)
        }
    })

   useEffect(() => {
        // 1. Guard check: Ensure editor and data are fully loaded
        if (!editor || chapterState.status !== "success") return;
        
        const data = chapterState.data.unwrap().unwrap();
        
        // 2. Update editor content if it doesn't match the database content
        if (editor.getHTML() !== data.content) {
            // We use a transaction fallback callback or queue to ensure order
            editor.commands.setContent(data.content);
        }

    }, [editor, chapterState]);



    const sidebarProps = useChapterEditorSidebarProps({
        storyId: params.storyId,
        state: storyChaptersState,
        selectedChapterId: params.chapterId,
        onChaptersRetry: refetchChapterList,
        onSelectChapter: (chapterId: string) => {
            navigate({
                to: "/stories/$storyId/$chapterId",
                params: { storyId: params.storyId, chapterId }
            })
        }
    })

    const onAskAgent = (query: string) => {
        const message = `I’m looking into “${query}” in my story. Find the most relevant scenes, explain how they connect, and point out anything inconsistent or worth developing.`

        setThreadCreationPending(true)
        createThread(
            {
                firstMessage: message
            },
            {
                onSuccess: async (newThread) => {
                    setThreadCreationPending(false)
                    await navigate({
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                            storyId: params.storyId,
                            threadId: newThread.threadId
                        },
                        search: {
                            prompt: message
                        }
                    })
                },
                onError: () => {
                    setThreadCreationPending(false)
                    error("Error", "Something went wrong and we could not investigate your pulse finding. The server might be experiencing issues.")
                }
            }
        )
    }

    const editorProps = useChapterEditorProps({
        updating: updating,
        query: query,
        threadCreationPending: threadCreationPending,
        onQueryChange: (query: string) => setQuery(query),
        onAskAgent: onAskAgent,
        onRetryChapter: refetchChapter,
        onRetryStory: refetchChapterList,
        editor: editor ? Some(editor) : None,
        storyId: params.storyId,
        state: chapterState
    })

    const commentsSidebarProps = useChapterCommentsSidebarProps({
        storyId: params.storyId,
        state: commentsState,
        onRefetchComments: refetchComments
    })

    return {
        sidebar: sidebarProps,
        editorProps: editorProps,
        tipTapEditor: editor,
        commentsSidebar: commentsSidebarProps
    }
}