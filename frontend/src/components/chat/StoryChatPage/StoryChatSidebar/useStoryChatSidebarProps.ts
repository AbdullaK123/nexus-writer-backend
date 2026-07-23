import { useNavigate } from "@tanstack/react-router";
import type { AsyncState, StoryDetailResponse, ThreadListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatSidebarProps } from "./StoryChatSidebar";
import { useState } from "react";
import { resolveAsyncStates } from "../../../../infrastructure/api/utils";
import { Option } from "oxide.ts"

export type UseStoryChatSidebarPropsArgs = 
{
    storyId: string
    threadId: Option<string>
    storyState: AsyncState<StoryDetailResponse, ApiError>,
    threadsState: AsyncState<ThreadListResponse, ApiError>
}

export function useStoryChatSidebarProps({
    storyId,
    threadId,
    storyState,
    threadsState
}: UseStoryChatSidebarPropsArgs): StoryChatSidebarProps {

    const navigate = useNavigate()

    const [open, setOpen] = useState(true)

    const resolvedState = resolveAsyncStates({
        story: storyState,
        threads: threadsState
    })

    
    switch (resolvedState.status) {
        case "idle": {
            return { status: "idle"}
        }
        case "empty": {
            return { status: "empty"}
        }
        case "error": {
            return { status: "error"}
        }
        case "loading": {
            return { status: "loading" }
        }
        case "success": {

            const data = resolvedState.data

            return {
                status: "ready",
                storyTitle: data.story.title,
                open: open,
                onOpenChange: (e: boolean) => setOpen(e),
                items: data.threads.threads.map((thread) => ({
                    storyId: storyId,
                    threadId: thread.threadId,
                    threadTitle: thread.threadTitle,
                    active: threadId.isSome() ? thread.threadId === threadId.unwrap() : false,
                    updatedAt: thread.updatedAt,
                    onSelected: () => navigate({ 
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                            storyId: storyId,
                            threadId: thread.threadId
                        }
                    })
                })),
                onNewThread: () => navigate({
                    to: "/stories/$storyId/chat/new",
                    params: {
                        storyId: storyId
                    }
                })
            }
        }
    }


}