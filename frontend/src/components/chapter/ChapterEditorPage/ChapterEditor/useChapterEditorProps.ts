import { useNavigate } from "@tanstack/react-router";
import { useCreateChapter, useStorySceneSearch } from "../../../../data/queries";
import type { AsyncState, ChapterContentResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { useSceneSearchPaletteProps } from "../../../story/SceneSearchPalette/useSceneSearchPaletteProps";
import type { ChapterEditorProps } from "./ChapterEditor";
import { type Editor } from "@tiptap/react";
import { None, Option, Some } from "oxide.ts"
import { useEffect, useEffectEvent, useState } from "react";
import { useToast } from "../../../common";
export type UseChapterEditorPropsArgs = 
{
    updating: boolean
    query: string
    onQueryChange: (query: string) => void
    onAskAgent: (query: string) => void
    onRetryStory: () => void
    onRetryChapter: () => void
    editor: Option<Editor>,
    storyId: string
    state: AsyncState<ChapterContentResponse, ApiError>
}


export function useChapterEditorProps({
    updating,
    query,
    onQueryChange,
    onAskAgent,
    onRetryChapter,
    onRetryStory,
    editor,
    storyId,
    state
}: UseChapterEditorPropsArgs): ChapterEditorProps {

    const [sceneSearchState, refetchScenes] = useStorySceneSearch(storyId, { query: query })
    const createChapterMutation = useCreateChapter(storyId)
    const searchPaletteProps = useSceneSearchPaletteProps({
        state: sceneSearchState,
        onRetry: refetchScenes,
        onAskAgent: onAskAgent,
        storyId: storyId,
        query: query,
        onQueryChange: onQueryChange
    })
    const [newChapterTitle, setNewChapterTitle] = useState("")
    const [modalOpen, setModalOpen] = useState(false)
    const { success, error } = useToast()
    const navigate = useNavigate()

    const onSearchError = useEffectEvent(() => {
        error("Failed to search your story", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {   
        if (sceneSearchState.status === "error") onSearchError()
    }, [sceneSearchState.status])

    switch (state.status) {
        case "idle":
        case "loading": {
            return {
                header: {
                    status: "loading"
                },
                content: {
                    status: "loading"
                },
                footer: {
                    status: "loading",
                    onAskAgent: onAskAgent,
                    searchPalette: searchPaletteProps
                }
            }
        }
        case "empty": {
            return {
                header: {
                    status: "empty"
                },
                content: {
                    status: "empty",
                },
                footer: {
                    status: "empty"  
                }
            }
        }
        case "error": {
            return {
                header: {
                    status: "error"
                },
                content: {
                    status: "error",
                    onRetryChapter: onRetryChapter,
                    onRetryStory: onRetryStory
                },
                footer: {
                    status: "error"
                }
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
                    editor: editor
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
                            params: {
                                storyId: storyId,
                                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                                chapterId: data.nextChapterId! 
                            }
                        })
                    }) : None,

                    onClickPreviousChapter: data.previousChapterId ? Some(() => {
                        navigate({
                            to: "/stories/$storyId/$chapterId",
                            params: {
                                storyId: storyId,
                                // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
                                chapterId: data.previousChapterId!
                            }
                        })
                    }) : None,

                    modalOpen: modalOpen,
                    onModalOpenChange: setModalOpen,
                    newChapterTitle: newChapterTitle,
                    onNewChapterTitleChange: setNewChapterTitle,
                    onNewChapter: (title) => {
                        createChapterMutation.mutate(
                        {
                            title: title,
                            content: ""
                        }, 
                        {
                            onSuccess: (newChapter) => {
                                success("Chapter created successfully!", "");
                                // Navigate to the brand new chapter
                                navigate({
                                    to: "/stories/$storyId/$chapterId",
                                    params: { storyId, chapterId: newChapter.id }
                                });
                            },
                            onError: () => {
                                error("Error", "Failed to create your chapter. The server might be experiencing issues.")
                            },
                            onSettled: () => {
                                setModalOpen(false)
                                setNewChapterTitle("")
                            }
                        });
                    }
                }
            }
        }
    }

}