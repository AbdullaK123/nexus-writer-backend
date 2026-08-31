import { useNavigate } from "@tanstack/react-router";
import { useCreateChapter, useStorySceneSearch } from "../../../../data/queries";
import type { AsyncState, ChapterContentResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { useSceneSearchPaletteProps } from "../../../story/SceneSearchPalette/useSceneSearchPaletteProps";
import type { ChapterEditorProps } from "./ChapterEditor";
import { type Editor } from "@tiptap/react";
import { None, Option, Some } from "oxide.ts"
import { useRef, useState } from "react";
import { useToast } from "../../../common";
import { useShortcut } from "../../../../hooks/useShortcut";
import { SingleFlightGate } from "../../../../shared/singleFlight";

export type UseChapterEditorPropsArgs = 
{
    updating: boolean
    query: string
    threadCreationPending: boolean
    onQueryChange: (query: string) => void
    onAskAgent: (query: string) => void
    editor: Option<Editor>,
    storyId: string
    state: AsyncState<ChapterContentResponse, ApiError>
}

export function useChapterEditorProps({
    updating,
    query,
    threadCreationPending,
    onQueryChange,
    onAskAgent,
    editor,
    storyId,
    state
}: UseChapterEditorPropsArgs): ChapterEditorProps {
    const [sceneSearchState, refetchScenes] = useStorySceneSearch(storyId, { query })
    const createChapterMutation = useCreateChapter(storyId)
    const createChapterGateRef = useRef(new SingleFlightGate())
    const searchPaletteProps = useSceneSearchPaletteProps({
        state: sceneSearchState,
        onRetry: refetchScenes,
        onAskAgent,
        storyId,
        query,
        onQueryChange,
        threadCreationPending
    })
    const [newChapterTitle, setNewChapterTitle] = useState("")
    const [modalOpen, setModalOpen] = useState(false)
    const { success, error } = useToast()
    const navigate = useNavigate()

    useShortcut(
        "ArrowLeft",
        true,
        false,
        () => {
            if (state.status === "success") {
                const data = state.data.unwrap().unwrap()
                if (data.previousChapterId) {
                    navigate({
                        to: "/stories/$storyId/$chapterId",
                        params: { storyId, chapterId: data.previousChapterId }
                    })
                }
            }
        }
    )

    useShortcut(
        "ArrowRight",
        true,
        false,
        () => {
            if (state.status === "success") {
                const data = state.data.unwrap().unwrap()
                if (data.nextChapterId) {
                    navigate({
                        to: "/stories/$storyId/$chapterId",
                        params: { storyId, chapterId: data.nextChapterId }
                    })
                }
            }
        }
    )

    useShortcut(
        "n",
        true,
        true,
        () => {
            if (state.status === "success") {
                const data = state.data.unwrap().unwrap()
                if (!data.nextChapterId) {
                    setNewChapterTitle(`Chapter ${data.chapterNumber + 1}`)
                    setModalOpen(true)
                }
            }
        }
    )

    switch (state.status) {
        case "idle":
        case "loading": {
            return {
                header: { status: "loading" },
                content: { status: "loading" },
                footer: { status: "loading" }
            }
        }
        case "empty": {
            return {
                header: { status: "empty" },
                content: { status: "empty" },
                footer: { status: "empty" }
            }
        }
        case "success": {
            const data = state.data.unwrap().unwrap()

            return {
                header: {
                    status: "ready",
                    saving: updating,
                    chapterNumber: data.chapterNumber,
                    chapterTitle: data.title
                },
                content: {
                    status: "ready",
                    editor
                },
                footer: {
                    status: "ready",
                    searchPalette: searchPaletteProps,
                    chapterNumber: data.chapterNumber,
                    prevChapterId: data.previousChapterId ? Some(data.previousChapterId) : None,
                    nextChapterId: data.nextChapterId ? Some(data.nextChapterId) : None,
                    onClickNextChapter: data.nextChapterId ? Some(() => {
                        navigate({
                            to: "/stories/$storyId/$chapterId",
                            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                            params: { storyId, chapterId: data.nextChapterId! }
                        })
                    }) : None,
                    onClickPreviousChapter: data.previousChapterId ? Some(() => {
                        navigate({
                            to: "/stories/$storyId/$chapterId",
                            // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                            params: { storyId, chapterId: data.previousChapterId! }
                        })
                    }) : None,
                    modalOpen,
                    onModalOpenChange: setModalOpen,
                    newChapterTitle,
                    onNewChapterTitleChange: setNewChapterTitle,
                    onNewChapter: (title) => {
                        if (!createChapterGateRef.current.tryStart()) return
                        createChapterMutation.mutate(
                            { title },
                            {
                                onSuccess: async (newChapter) => {
                                    success("Chapter created successfully!", "");
                                    setTimeout(() => navigate({
                                        to: "/stories/$storyId/$chapterId",
                                        params: { storyId, chapterId: newChapter.id }
                                    }), 1000);
                                },
                                onError: () => {
                                    error("Error", "Failed to create your chapter. The server might be experiencing issues.")
                                },
                                onSettled: () => {
                                    createChapterGateRef.current.finish()
                                    setModalOpen(false)
                                    setNewChapterTitle("")
                                }
                            }
                        );
                    }
                }
            }
        }
    }
}
