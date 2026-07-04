import { useParams } from "@tanstack/react-router";
import { useChapter, useStoryChapters, useUpdateChapter } from "../../../data/queries";
import type { ChapterEditorProps } from "./ChapterEditor";
import { useChapterEditorSidebarProps, type ChapterEditorSidebarProps } from "./ChapterEditorSidebar";
import { useEffect, useMemo, useState } from "react";
import { useEditor } from "@tiptap/react";
import { StarterKit } from "@tiptap/starter-kit";
import { debounce } from "lodash"
import { useChapterEditorProps } from "./ChapterEditor"
import { None, Some } from "oxide.ts";
export type ChapterEditorPageProps = {
    sidebar: ChapterEditorSidebarProps
    editor: ChapterEditorProps
}

export function useChapterEditorPage(): ChapterEditorPageProps {

    const params = useParams({ from: "/app/stories/$storyId/$chapterId" })

    const [selectedChapterId, setSelectedChapterId] = useState(() => params.chapterId)
    const [storyChaptersState, refetchChapterList] = useStoryChapters(params.storyId)
    const [chapterState, refetchChapter] = useChapter(selectedChapterId)
    const updateChapterMutation = useUpdateChapter(selectedChapterId)
    const [updating, setUpdating] = useState(false)
    const [query, setQuery] = useState("")

    const debouncedUpdate = useMemo(
        () => debounce((htmlContent: string) => {
            setUpdating(true)
            updateChapterMutation.mutate(
                { content: htmlContent },
                {
                    onSettled: () => setUpdating(false)
                }
            );
        }, 2000),
        [updateChapterMutation] // Re-create only if the mutation reference changes
    );
    
    useEffect(() => {
        return () => debouncedUpdate.cancel();
    }, [debouncedUpdate]);

    const editor = useEditor({
        extensions: [StarterKit],
        content: (() => {
            if (chapterState.status === "success") {
                const data = chapterState.data.unwrap().unwrap()
                return data.content
            } else {
                return ""
            }
        })(),
        onUpdate: ({ editor }) => {
            const html = editor.getHTML()
            debouncedUpdate(html)
        }
    })

    const sidebarProps = useChapterEditorSidebarProps({
        state: storyChaptersState,
        selectedChapterId: selectedChapterId,
        onSelectChapter: (chapterId: string) => setSelectedChapterId(chapterId)
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
        editor: editorProps
    }
}