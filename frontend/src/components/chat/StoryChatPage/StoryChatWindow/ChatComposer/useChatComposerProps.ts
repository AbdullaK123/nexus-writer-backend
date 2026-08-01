import { useState } from "react";
import { useCreateThread } from "../../../../../data/queries";
import { useNavigate } from "@tanstack/react-router";
import type { ChatComposerProps } from "./ChatComposer";
import { useToast } from "../../../../common";


export type UseStoryChatWindowPropsArgs = {
    storyId: string;
};

export function useChatComposerProps({
    storyId
}: UseStoryChatWindowPropsArgs): ChatComposerProps {

    const [threadCreationPending, setThreadCreationPending] = useState(false)

    const [query, setQuery] = useState("");

    const { error } = useToast()

    const {
        mutate: createThread
    } = useCreateThread(storyId)

    const navigate = useNavigate()

    const onUserPromptSubmitted = (query: string) => {

        setThreadCreationPending(true)

        createThread(
            {
                firstMessage: query
            },
            {
                onSuccess: async (newThread) => {
                    setThreadCreationPending(false)
                    await navigate({
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                            storyId: storyId,
                            threadId: newThread.threadId
                        },
                        search: {
                            prompt: query
                        }
                    })
                },
                onError:  () => {
                    setThreadCreationPending(false)
                    error("Failed to create thread.", "Something went wrong. The server might be experiencing issues.")           
                }
            }
        )
    }

    return {
        status: "ready",
        threadCreationPending: threadCreationPending,
        query: query,
        onQueryChange: (query: string) => setQuery(query),
        onEnterDown: (query: string) => onUserPromptSubmitted(query),
        onSubmit: (query: string) => onUserPromptSubmitted(query)
    }
}
