import { useParams } from "@tanstack/react-router";
import { useStoryChatSidebarProps, type StoryChatSidebarProps } from "./StoryChatSidebar";
import { useStoryDetails,  useThreads } from "../../../data/queries";
import type { ChatComposerProps } from "./StoryChatWindow/ChatComposer/ChatComposer";
import { useChatComposerProps } from "./StoryChatWindow/ChatComposer/useChatComposerProps";
import { None } from "oxide.ts";
import { useEffect, useEffectEvent } from "react";
import { useToast } from "../../common";



export type NewStoryChatPageProps = 
{
    sidebar: StoryChatSidebarProps
    composer: ChatComposerProps
}


export function useNewStoryChatPage(): NewStoryChatPageProps {

    const params = useParams({ from: "/app/stories/$storyId/chat/new" })

    const { error } = useToast()

    const [
        threadsState,
        refetchThreads
    ] = useThreads(params.storyId)

    const [
        storyState,
        refetchStory
    ] = useStoryDetails(params.storyId)

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
        if (storyState.status === "error") onStoryError()
    }, [storyState.status])

    const refetchSidebarData = () => {
        refetchThreads()
        refetchStory()
    }

    const sidebarProps = useStoryChatSidebarProps({
        storyId: params.storyId,
        threadId: None,
        storyState: storyState,
        threadsState: threadsState,
        onRetry: refetchSidebarData
    })

    const composer = useChatComposerProps({
        storyId: params.storyId
    })


    return {
        sidebar: sidebarProps,
        composer: composer
    }
}