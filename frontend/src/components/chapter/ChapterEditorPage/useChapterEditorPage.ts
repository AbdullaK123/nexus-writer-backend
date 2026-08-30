import { useNavigate, useParams } from "@tanstack/react-router";
import { useChapter, useChapterComments, useCreateThread, useStoryChapters, useUpdateChapter } from "../../../data/queries";
import type { ChapterEditorProps } from "./ChapterEditor";
import { useChapterEditorSidebarProps, type ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useEffect, useMemo, useRef, useState } from "react";
import { Editor, useEditor } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { debounce } from "lodash"
import { useChapterEditorProps } from "./ChapterEditor"
import { None, Some } from "oxide.ts";
import { useToast } from "../../common";
import type { ChapterCommentsSidebarProps } from "./ChapterCommentsSidebar/ChapterCommentsSidebar";
import { useChapterCommentsSidebarProps } from "./ChapterCommentsSidebar";
import { useSettings } from "../../../data/providers";
import { LatestOperation } from "../../../shared/latestOperation";
import { SingleFlightGate } from "../../../shared/singleFlight";
import { isCurrentChapter } from "./chapterIdentity";
import { hydrateChapterContent } from "./chapterHydration";

export type ChapterEditorPageProps = {
    sidebar: ChapterEditorSidebarProps
    editorProps: ChapterEditorProps
    tipTapEditor: Editor,
    commentsSidebar: ChapterCommentsSidebarProps
}

export function useChapterEditorPage(): ChapterEditorPageProps {
    const params = useParams({ from: "/app/stories/$storyId/$chapterId" })
    const storyChaptersState = useStoryChapters(params.storyId)
    const chapterBelongsToStory = storyChaptersState.status === "success"
        && storyChaptersState.data.unwrap().unwrap().chapters.some(
            (chapter) => chapter.chapterId === params.chapterId
        )
    const chapterState = useChapter(params.chapterId, true, chapterBelongsToStory)
    const commentsState = useChapterComments(params.chapterId, chapterBelongsToStory)
    const updateChapterMutation = useUpdateChapter(params.chapterId)
    const [updating, setUpdating] = useState(false)
    const [query, setQuery] = useState("")
    const [threadCreationPending, setThreadCreationPending] = useState(false)
    const saveTrackerRef = useRef(new LatestOperation())
    const hydratedChapterRef = useRef<string | null>(null)
    const threadGateRef = useRef(new SingleFlightGate())
    const { mutate: createThread } = useCreateThread(params.storyId)
    const navigate = useNavigate()
    const { settings } = useSettings()
    const { error } = useToast()

    useEffect(() => {
        if (storyChaptersState.status !== "success" || chapterBelongsToStory) return
        void navigate({ to: "/404", search: { redirect: `/stories/${params.storyId}/${params.chapterId}` } })
    }, [storyChaptersState.status, chapterBelongsToStory, navigate, params.storyId, params.chapterId])

    const debouncedUpdate = useMemo(
        // eslint-disable-next-line react-hooks/refs
        () => debounce((htmlContent: string) => {
            const revision = saveTrackerRef.current.start()
            setUpdating(true)
            updateChapterMutation.mutate(
                { content: htmlContent },
                {
                    onSettled: () => {
                        if (saveTrackerRef.current.isLatest(revision)) {
                            setUpdating(false)
                        }
                    }
                }
            );
        }, 500),
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [params.chapterId, updateChapterMutation.mutate]
    );

    useEffect(() => {
        saveTrackerRef.current.invalidate()
        setUpdating(false)

        return () => {
            debouncedUpdate.flush()
            debouncedUpdate.cancel()
        }
    }, [params.chapterId, debouncedUpdate]);

    const editor = useEditor({
        extensions: [StarterKit],
        content: "",
        editorProps: {
            attributes: {
                style: settings.isSome() ? `
                        font-family: "${settings.unwrap().editor.font_family}";
                        font-size: ${settings.unwrap().editor.font_size}px;
                        line-height: ${settings.unwrap().editor.line_height};
                        max-width: ${settings.unwrap().editor.content_width}px;
                        width: 100%;
                        margin: 0 auto;
                    `: '',
                spellcheck: settings.isSome() ? settings.unwrap().editor.spellcheck ? "true" : "false" : "false",
            }
        },
        onUpdate: ({ editor }) => {
            debouncedUpdate(editor.getHTML())
        }
    })

    useEffect(() => {
        if (!editor) return
        editor.setOptions({
            editorProps: {
                attributes: {
                    style: settings.isSome() ? `
                    font-family: "${settings.unwrap().editor.font_family}";
                    font-size: ${settings.unwrap().editor.font_size}px;
                    line-height: ${settings.unwrap().editor.line_height};
                    max-width: ${settings.unwrap().editor.content_width}px;
                    width: 100%;
                    margin: 0 auto;
                `: '',
                spellcheck: settings.isSome() ? settings.unwrap().editor.spellcheck ? "true" : "false" : "false",
            },
        },
    })
    }, [editor, settings])

    useEffect(() => {
        if (!editor || chapterState.status !== "success") return;
        const data = chapterState.data.unwrap().unwrap();
        if (!isCurrentChapter(params.chapterId, data.id)) return
        if (hydratedChapterRef.current === data.id) return

        hydrateChapterContent(editor, data.content);
        hydratedChapterRef.current = data.id
    }, [editor, chapterState, params.chapterId]);

    const sidebarProps = useChapterEditorSidebarProps({
        storyId: params.storyId,
        state: storyChaptersState,
        selectedChapterId: params.chapterId,
        onSelectChapter: (chapterId: string) => {
            navigate({
                to: "/stories/$storyId/$chapterId",
                params: { storyId: params.storyId, chapterId }
            })
        }
    })

    const onAskAgent = (agentQuery: string) => {
        if (!threadGateRef.current.tryStart()) return
        const message = `I’m looking into “${agentQuery}” in my story. Find the most relevant scenes, explain how they connect, and point out anything inconsistent or worth developing.`

        setThreadCreationPending(true)
        createThread(
            { firstMessage: message },
            {
                onSuccess: async (newThread) => {
                    threadGateRef.current.finish()
                    setThreadCreationPending(false)
                    await navigate({
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                            storyId: params.storyId,
                            threadId: newThread.threadId
                        },
                        search: { prompt: message }
                    })
                },
                onError: () => {
                    threadGateRef.current.finish()
                    setThreadCreationPending(false)
                    error("Error", "Something went wrong and we could not investigate your pulse finding. The server might be experiencing issues.")
                }
            }
        )
    }

    const editorProps = useChapterEditorProps({
        updating,
        query,
        threadCreationPending,
        onQueryChange: setQuery,
        onAskAgent,
        editor: editor ? Some(editor) : None,
        storyId: params.storyId,
        state: chapterState
    })

    const commentsSidebarProps = useChapterCommentsSidebarProps({
        storyId: params.storyId,
        state: commentsState
    })

    return {
        sidebar: sidebarProps,
        editorProps,
        tipTapEditor: editor,
        commentsSidebar: commentsSidebarProps
    }
}
