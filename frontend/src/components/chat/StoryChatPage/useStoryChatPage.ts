import { useParams, useRouteContext } from "@tanstack/react-router";
import type { StoryChatHeaderProps } from "./StoryChatHeader";
import { useStoryChatSidebarProps, type StoryChatSidebarProps } from "./StoryChatSidebar";
import { useStoryChatWindowProps, type StoryChatWindowProps } from "./StoryChatWindow";
import { useStoryDetails, useThreadMessages, useThreads } from "../../../data/queries";
import { Some, None } from "oxide.ts"
import { useStoryChatHeaderProps } from "./StoryChatHeader/useStoryChatHeaderProps";

export type StoryChatPageProps = {
    header: StoryChatHeaderProps
    sidebar: StoryChatSidebarProps
    window: StoryChatWindowProps
}

export function useStoryChatPage(): StoryChatPageProps {
    const params = useParams({ from: "/app/stories/$storyId/chat/$threadId" })
    const ctx = useRouteContext({ from: "/app/stories/$storyId/chat/$threadId" })
    const [conversationState, refetchMessages] = useThreadMessages(params.storyId, params.threadId)
    const threadsState = useThreads(params.storyId)
    const storyState = useStoryDetails(params.storyId)

    const headerProps = useStoryChatHeaderProps({
        storyId: params.storyId,
        threadId: params.threadId,
        conversationState,
        storyState
    })

    const sidebarProps = useStoryChatSidebarProps({
        storyId: params.storyId,
        threadId: Some(params.threadId),
        storyState,
        threadsState
    })

    const windowProps = useStoryChatWindowProps({
        storyId: params.storyId,
        threadId: params.threadId,
        user: ctx.auth.status === "authenticated" ? Some(ctx.auth.user) : None,
        conversationState,
        onRetry: () => {
            refetchMessages()
        }
    })

    return {
        header: headerProps,
        sidebar: sidebarProps,
        window: windowProps
    }
}
