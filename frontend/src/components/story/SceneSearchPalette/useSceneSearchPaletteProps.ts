import { useNavigate } from "@tanstack/react-router";
import type { AsyncState, SceneSearchListResponse } from "../../../infrastructure/api/types";
import type { ApiError } from "../../../shared/types";
import type { SceneSearchPaletteProps } from "./SceneSearchPalette";

export type UseSceneSearchPalettePropsArgs = 
{
    storyId: string
    query: string
    onQueryChange: (query: string) => void
    onAskAgent: (query: string) => void
    onRetry: () => void
    state: AsyncState<SceneSearchListResponse, ApiError>
}


export function useSceneSearchPaletteProps({
    storyId,
    query,
    onQueryChange,
    onAskAgent,
    onRetry,
    state
}: UseSceneSearchPalettePropsArgs): SceneSearchPaletteProps {
    
    const navigate = useNavigate( )

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
                            navigate({ to: `/stories/${storyId}/${chapterId}`})
                            // handle selecting text between startQuote and endQuote
                        }
                    },
                    footer: {
                        query: query,
                        onAskAgent: onAskAgent
                    }
                }
            }
        }
    }
}   