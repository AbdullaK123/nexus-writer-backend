import { useParams } from "@tanstack/react-router";
import { useStoryChatSidebarProps, type StoryChatSidebarProps } from "./StoryChatSidebar";
import { useStoryDetails,  useThreads } from "../../../data/queries";
import type { ChatComposerProps } from "./StoryChatWindow/ChatComposer/ChatComposer";
import { useChatComposerProps } from "./StoryChatWindow/ChatComposer/useChatComposerProps";
import { None } from "oxide.ts";



export type NewStoryChatPageProps = 
{
    sidebar: StoryChatSidebarProps
    composer: ChatComposerProps
}


export function useNewStoryChatPage(): NewStoryChatPageProps {

    const params = useParams({ from: "/app/stories/$storyId/chat/new" })

    const [
        threadsState,
        _
    ] = useThreads(params.storyId)

    const [
        storyState,
        __
    ] = useStoryDetails(params.storyId)

    const sidebarProps = useStoryChatSidebarProps({
        storyId: params.storyId,
        threadId: None,
        storyState: storyState,
        threadsState: threadsState
    })

    const composer = useChatComposerProps({
        storyId: params.storyId
    })


    return {
        sidebar: sidebarProps,
        composer: composer
    }
}