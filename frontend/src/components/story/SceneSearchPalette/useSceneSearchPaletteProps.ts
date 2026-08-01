import { useNavigate } from "@tanstack/react-router";
import type { AsyncState, SceneSearchListResponse } from "../../../infrastructure/api/types";
import type { ApiError } from "../../../shared/types";
import type { SceneSearchPaletteProps } from "./SceneSearchPalette";
import { triggerPaletteClose } from "./eventbus";

export type UseSceneSearchPalettePropsArgs = 
{
    storyId: string
    query: string
    onQueryChange: (query: string) => void
    onAskAgent: (query: string) => void
    onRetry: () => void
    threadCreationPending: boolean
    state: AsyncState<SceneSearchListResponse, ApiError>
}


export function useSceneSearchPaletteProps({
    storyId,
    query,
    onQueryChange,
    onAskAgent,
    onRetry,
    threadCreationPending,
    state
}: UseSceneSearchPalettePropsArgs): SceneSearchPaletteProps {
    
    const navigate = useNavigate()

    switch (state.status) {
        case "idle":
        case "loading": {
            return {
                query: query,
                onQueryChange: onQueryChange,
                content: {
                    header: {
                        query: query,
                        onQueryChange: onQueryChange
                    },
                    list: {
                        status: "loading"
                    },
                    footer: {
                        threadCreationPending: threadCreationPending,
                        query: query,
                        onAskAgent: onAskAgent
                    }
                }
            }
        }
        case "empty": {
             return {
                query: query,
                onQueryChange: onQueryChange,
                content: {
                    header: {
                        query: query,
                        onQueryChange: onQueryChange
                    },
                    list: {
                        status: "empty"
                    },
                    footer: {
                        threadCreationPending: threadCreationPending,
                        query: query,
                        onAskAgent: onAskAgent
                    }
                }
            }
        }
        case "error": {
            return {
                query: query,
                onQueryChange: onQueryChange,
                content: {
                    header: {
                        query: query,
                        onQueryChange: onQueryChange
                    },
                    list: {
                        status: "error",
                        onRetry: onRetry
                    },
                    footer: {
                        threadCreationPending: threadCreationPending,
                        query: query,
                        onAskAgent: onAskAgent
                    }
                }
            }
        }
        case "success": {

            const data = state.data.unwrap().unwrap().results

            return {
                query: query,
                onQueryChange: onQueryChange,
                content: {
                    header: {
                        query: query,
                        onQueryChange: onQueryChange
                    },
                    list: {
                        status: "ready",
                        results: data,
                        onSelectResult: (chapterId: string) => {

                            navigate({
                                to: "/stories/$storyId/$chapterId",
                                params: {
                                    storyId,
                                    chapterId: chapterId,
                                },
                            })

                            triggerPaletteClose()
                        }
                    },
                    footer: {
                        threadCreationPending: threadCreationPending,
                        query: query,
                        onAskAgent: onAskAgent
                    }
                }
            }
        }
    }
}   