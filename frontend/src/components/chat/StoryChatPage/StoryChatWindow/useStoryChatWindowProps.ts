import { useState, useEffect, useRef, useMemo } from "react";
import type { AsyncState, ChatMessageListResponse, UserResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatWindowProps, ConversationMessage } from "./StoryChatWindow";
import { streamSse } from "../../../../infrastructure/sse";
import { loadConfig } from "../../../../infrastructure/config";
import { None, Some } from "oxide.ts";
import type { EventSourceMessage } from "eventsource-parser";
import { useCreateThread } from "../../../../data/queries";
import { useNavigate } from "@tanstack/react-router";

const config = loadConfig().unwrap();

export type UseStoryChatWindowPropsArgs = {
    storyId: string;
    threadId: string;
    conversationState: AsyncState<ChatMessageListResponse, ApiError>;
    user: UserResponse;
    onRetry: () => void;
};

export function useStoryChatWindowProps({
    storyId,
    threadId,
    conversationState,
    user,
    onRetry,
}: UseStoryChatWindowPropsArgs): StoryChatWindowProps {

    const [query, setQuery] = useState("");

    const {
        mutate: createThread
    } = useCreateThread(storyId)

    const navigate = useNavigate()

    const [streamingMessages, setStreamingMessages] = useState<ConversationMessage[]>([]);
    
    const streamCancellerRef = useRef<AbortController>(new AbortController());

    const historicalMessages = useMemo<ConversationMessage[]>(() => {
        if (conversationState.status !== "success") return [];

        const data = conversationState.data.unwrap().unwrap();
        if (data.messages.length === 0) return [];

        const conversationMessages: ConversationMessage[] = [];

        data.messages.forEach((msg) => {
            switch (msg.kind) {
                case "request": {
                    msg.message.parts.forEach((part) => {
                        if (part.part_kind === "user-prompt") {
                            conversationMessages.push({
                                type: "user",
                                props: {
                                    user: user,
                                    createdAt: new Date(part.timestamp),
                                    message: part.content as string
                                }
                            });
                        }
                    });
                    return;
                }
                case "response": {
                    msg.message.parts.forEach((part) => {
                        if (part.part_kind === "text") {
                            conversationMessages.push({
                                type: "assistant",
                                props: {
                                    status: "done",
                                    message: part.content as string
                                }
                            });
                        }
                    });
                    return;
                }
            }
        });

        return conversationMessages;
    }, [conversationState, user]);


    const allMessages = useMemo(() => {
        return [...historicalMessages, ...streamingMessages];
    }, [historicalMessages, streamingMessages]);

    // Cleanup abort controller on component unmount
    useEffect(() => {
        return () => streamCancellerRef.current.abort();
    }, []);

    const onNewThreadCreated = (query: string) => {

        streamCancellerRef.current.abort();
        streamCancellerRef.current = new AbortController();

        const started = performance.now();
        setQuery("");

        setStreamingMessages([
            {
                type: "user",
                props: {
                    user: user,
                    createdAt: new Date(),
                    message: query
                }
            },
            {
                type: "assistant",
                props: {
                    status: "streaming",
                    message: ""
                }
            }
        ]);

        streamSse(
            {
                url: `${config.api.baseURL}/api/stories/${storyId}/threads/${threadId}/turn`,
                method: Some("POST"),
                body: Some({
                    user_message: query
                }),
                signal: Some(streamCancellerRef.current.signal),
                headers: None
            },
            {
                onEvent: (event: EventSourceMessage) => {
                    switch (event.event) {
                        case "token": {
                            const data = JSON.parse(event.data);
                            setStreamingMessages(prev => prev.map((msg, idx) => {
                                if (idx === prev.length - 1) {
                                    return {
                                        type: "assistant",
                                        props: {
                                            status: "streaming",
                                            message: msg.props.message + data.delta
                                        }
                                    };
                                } else {
                                    return msg;
                                }
                            }));
                            break;
                        }
                    }
                },
                onClose: Some(() => {
                    setStreamingMessages([]);
                    onRetry(); 
                })
            }
        ).then((result) => {
            console.log(`SSE stream finished in ${((performance.now() - started) / 1000).toFixed(2)}s`);
            if (result.isErr()) {
                const e = result.unwrapErr();
                switch (e._tag) {
                    case "SseAbortedError":
                        console.log("Aborted SSE stream");
                        return;
                    case "SseHttpError":
                        console.log(`HTTP Error!`);
                        return;
                    case "SseNetworkError":
                        console.log("Network Error!");
                        return;
                    case "SseNoBodyError":
                        console.log("NO BODY!");
                        return;
                    case "SseStreamError":
                        console.log("OMG STREAM ERROR!");
                        return;
                }
            }
        });
    };

    const onUserPromptSubmitted = (query: string) => {
        createThread(
            {
                firstMessage: query
            },
            {
                onSuccess: async (newThread) => {
                    await navigate({
                        to: "/stories/$storyId/chat/$threadId",
                        params: {
                            storyId: storyId,
                            threadId: newThread.threadId
                        }
                    })
                    onNewThreadCreated(query)
                }
            }
        )
    }

    switch (conversationState.status) {
        case "empty": {
            return {
                status: "empty",
                composer: {
                    status: "ready",
                    query: query,
                    onQueryChange: (query: string) => setQuery(query),
                    onEnterDown: (query: string) => onUserPromptSubmitted(query),
                    onSubmit: (query: string) => onUserPromptSubmitted(query)
                }
            };
        }
        case "idle": {
            return {
                status: "empty",
                composer: {
                    status: "empty"
                }
            };
        }
        case "error": {
            return {
                status: "error",
                onRetry: onRetry
            };
        }
        case "success": {
            return {
                status: "ready",
                messages: allMessages, 
                composer: {
                    status: streamingMessages.length > 0 ? "loading" : "ready",
                    query: query,
                    onQueryChange: (query: string) => setQuery(query),
                    onEnterDown: (query: string) => onUserPromptSubmitted(query),
                    onSubmit: (query: string) => onUserPromptSubmitted(query)
                }
            };
        }
        default: {
            return {
                status: "empty",
                composer: {
                    status: "empty"
                }
            };
        }
    }
}
