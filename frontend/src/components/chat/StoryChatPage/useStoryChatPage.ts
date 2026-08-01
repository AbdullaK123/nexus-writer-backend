import { useParams, useRouteContext } from "@tanstack/react-router";
import type { StoryChatHeaderProps } from "./StoryChatHeader";
import { useStoryChatSidebarProps, type StoryChatSidebarProps } from "./StoryChatSidebar";
import { useStoryChatWindowProps, type StoryChatWindowProps } from "./StoryChatWindow";
import { useStoryDetails, useThreadMessages, useThreads } from "../../../data/queries";
import { Some, None } from "oxide.ts"
import { useStoryChatHeaderProps } from "./StoryChatHeader/useStoryChatHeaderProps";
import { useEffect, useEffectEvent } from "react";
import { useToast } from "../../common";



export type StoryChatPageProps = 
{
    header: StoryChatHeaderProps
    sidebar: StoryChatSidebarProps
    window: StoryChatWindowProps
}


export function useStoryChatPage(): StoryChatPageProps {

    const params = useParams({ from: "/app/stories/$storyId/chat/$threadId" })

    const ctx = useRouteContext({ from: "/app/stories/$storyId/chat/$threadId" })

    const { error } = useToast()

    const [
        conversationState, 
        refetchMessages
    ] = useThreadMessages(params.storyId, params.threadId)

    const [
        threadsState,
        refetchThreads
    ] = useThreads(params.storyId)

    const [
        storyState,
        refetchStory
    ] = useStoryDetails(params.storyId)

    const refetchSidebarData = () => {
        refetchStory()
        refetchThreads()
    }

    const refetchHeaderData = () => {
        refetchStory()
        refetchMessages()
    }

    const onConversationError = useEffectEvent(() => {
        error("Failed to fetch conversation", "Something went wrong. The server might be experiencing issues.")
    })

    const onThreadsError = useEffectEvent(() => {
        error("Failed to fetch threads", "Something went wrong. The server might be experiencing issues.")
    })

    const onStoryError = useEffectEvent(() => {
        error("Failed to fetch story", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (threadsState.status === "error") onThreadsError()
    }, [threadsState.status])

    useEffect(() => {
        if (conversationState.status === "error") onConversationError()
    }, [conversationState.status])

    useEffect(() => {
        if (storyState.status === "error") onStoryError()
    }, [storyState.status])

    const headerProps = useStoryChatHeaderProps({
        storyId: params.storyId,
        threadId: params.threadId,
        conversationState: conversationState,
        storyState: storyState,
        onRetry: refetchHeaderData
    })

    const sidebarProps = useStoryChatSidebarProps({
        storyId: params.storyId,
        threadId: Some(params.threadId),
        storyState: storyState,
        threadsState: threadsState,
        onRetry: refetchSidebarData
    })

    const windowProps = useStoryChatWindowProps({
        storyId: params.storyId,
        threadId: params.threadId,
        user: (ctx.auth.status === "authenticated") ? Some(ctx.auth.user) : None,
        conversationState: conversationState,
        onRetry: () => {
            refetchMessages()
            refetchStory()
            refetchThreads()
        }
    })


    return {
        header: headerProps,
        sidebar: sidebarProps,
        window: windowProps
    }
}