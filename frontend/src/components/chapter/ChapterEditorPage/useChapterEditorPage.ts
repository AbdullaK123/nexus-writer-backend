import { useNavigate, useParams } from "@tanstack/react-router";
import { useChapter, useStoryChapters, useUpdateChapter } from "../../../data/queries";
import type { ChapterEditorProps } from "./ChapterEditor";
import { useChapterEditorSidebarProps, type ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useEffect, useMemo, useState } from "react";
import { Editor, useEditor } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { debounce } from "lodash"
import { useChapterEditorProps } from "./ChapterEditor"
import { None, Some } from "oxide.ts";
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
        [updateChapterMutation] // Re-create only if the mutation reference changes
    );
    
    useEffect(() => {
        return () => debouncedUpdate.cancel();
    }, [debouncedUpdate]);

    const editor = useEditor({
        extensions: [StarterKit],
        content: "", // Start clean or let the hook handle it
        onUpdate: ({ editor }) => {
            const html = editor.getHTML()
            debouncedUpdate(html)
        }
    })

    useEffect(() => {
        if (editor && chapterState.status === "success") {
            const data = chapterState.data.unwrap().unwrap()
            
            if (editor.getHTML() !== data.content) {
                editor.commands.setContent(data.content)
            }
        }
    }, [editor, chapterState, params.chapterId]) 


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