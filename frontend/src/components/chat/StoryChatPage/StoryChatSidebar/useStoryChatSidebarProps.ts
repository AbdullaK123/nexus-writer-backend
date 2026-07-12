import { useNavigate } from "@tanstack/react-router";
import type { AsyncState, ThreadListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatSidebarProps } from "./StoryChatSidebar";
import { useState } from "react";


export type UseStoryChatSidebarPropsArgs = 
{
    storyId: string
    storyTitle: string
    threadsState: AsyncState<ThreadListResponse, ApiError>
}

export function useStoryChatSidebarProps({
    storyId,
    storyTitle,
    threadsState
}: UseStoryChatSidebarPropsArgs): StoryChatSidebarProps {

    const navigate = useNavigate()

    const [open, setOpen] = useState(true)

    
    switch (threadsState.status) {
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

            const data = threadsState.data.unwrap().unwrap()

            return {
                status: "ready",
                storyTitle: storyTitle,
                open: open,
                onOpenChange: (e: boolean) => setOpen(e),
                items: data.threads.map((thread) => ({
                    storyId: storyId,
                    threadId: thread.threadId,
                    threadTitle: thread.threadTitle,
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