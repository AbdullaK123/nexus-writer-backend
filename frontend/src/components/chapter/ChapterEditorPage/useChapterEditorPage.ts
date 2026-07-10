import { useNavigate, useParams } from "@tanstack/react-router";
import { useChapter, useStoryChapters, useUpdateChapter } from "../../../data/queries";
import type { ChapterEditorProps } from "./ChapterEditor";
import { useChapterEditorSidebarProps, type ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useEffect, useEffectEvent, useMemo, useState } from "react";
import { Editor, useEditor } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { debounce } from "lodash"
import { useChapterEditorProps } from "./ChapterEditor"
import { None, Some } from "oxide.ts";
import { useToast } from "../../common";
export type ChapterEditorPageProps = {
    sidebar: ChapterEditorSidebarProps
    editorProps: ChapterEditorProps
    tipTapEditor: Editor
}

export function useChapterEditorPage(): ChapterEditorPageProps {

    const params = useParams({ from: "/app/stories/$storyId/$chapterId" })

    const [storyChaptersState, refetchChapterList] = useStoryChapters(params.storyId)
    const [chapterState, refetchChapter] = useChapter(params.chapterId)
    const updateChapterMutation = useUpdateChapter(params.chapterId)
    const [updating, setUpdating] = useState(false)
    const [query, setQuery] = useState("")
    const navigate = useNavigate()

    const { error } = useToast()

    const onStoryChaptersError = useEffectEvent(() => {
        error("Failed to fetch your chapters", "Somthing went wrong. The server might be experiencing issues.")
    })

    const onChapterError = useEffectEvent(() => {
        error("Failed to load your chapter", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (storyChaptersState.status === "error") onStoryChaptersError()
    }, [storyChaptersState.status])

    useEffect(() => {
        if (chapterState.status === "error") onChapterError()
    }, [chapterState.status])

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
        state: storyChaptersState,
        selectedChapterId: params.chapterId,
         onSelectChapter: (chapterId: string) => {
            navigate({
                to: "/stories/$storyId/$chapterId",
                params: { storyId: params.storyId, chapterId }
            })
        }
    })

    const editorProps = useChapterEditorProps({
        updating: updating,
        query: query,
        onQueryChange: (query: string) => setQuery(query),
        onAskAgent: (query: string) => console.log(query),
        onRetryChapter: refetchChapter,
        onRetryStory: refetchChapterList,
        editor: editor ? Some(editor) : None,
        storyId: params.storyId,
        state: chapterState
    })

    return {
        sidebar: sidebarProps,
        editorProps: editorProps,
        tipTapEditor: editor
    }
}