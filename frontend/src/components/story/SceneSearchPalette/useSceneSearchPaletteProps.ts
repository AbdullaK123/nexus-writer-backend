import { useNavigate } from "@tanstack/react-router";
import type { AsyncState, SceneSearchListResponse } from "../../../infrastructure/api/types";
import type { ApiError } from "../../../shared/types";
import type { SceneSearchPaletteProps } from "./SceneSearchPalette";
import { triggerPaletteClose } from "./eventbus";

export type UseSceneSearchPalettePropsArgs = {
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
    threadCreationPending,
    state
}: UseSceneSearchPalettePropsArgs): SceneSearchPaletteProps {
    const navigate = useNavigate()

    switch (state.status) {
        case "idle":
        case "loading":
            return {
                query,
                onQueryChange,
                content: {
                    header: { query, onQueryChange },
                    list: { status: "loading" },
                    footer: { threadCreationPending, query, onAskAgent }
                }
            }
        case "empty":
             return {
                query,
                onQueryChange,
                content: {
                    header: { query, onQueryChange },
                    list: { status: "empty" },
                    footer: { threadCreationPending, query, onAskAgent }
                }
            }
        case "success": {
            const data = state.data.unwrap().unwrap().results
            return {
                query,
                onQueryChange,
                content: {
                    header: { query, onQueryChange },
                    list: {
                        status: "ready",
                        results: data,
                        onSelectResult: (chapterId: string) => {
                            navigate({
                                to: "/stories/$storyId/$chapterId",
                                params: { storyId, chapterId },
                            })
                            triggerPaletteClose()
                        }
                    },
                    footer: { threadCreationPending, query, onAskAgent }
                }
            }
        }
    }
}
