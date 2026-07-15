import { useState, useEffect, useRef, useCallback, useMemo, startTransition } from "react";
import type { AsyncState, ChatMessageListResponse, UserResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatWindowProps, ConversationMessage } from "./StoryChatWindow";
import { streamSse } from "../../../../infrastructure/sse";
import { None, Some, Option } from "oxide.ts";
import type { EventSourceMessage } from "eventsource-parser";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useToast } from "../../../common";

export type UseStoryChatWindowPropsArgs = {
    storyId: string;
    threadId: string;
    conversationState: AsyncState<ChatMessageListResponse, ApiError>;
    user: Option<UserResponse>;
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

    const navigate = useNavigate({ from: "/stories/$storyId/chat/$threadId"})

    const search = useSearch({ from: "/app/stories/$storyId/chat/$threadId" })

    const [streamingMessages, setStreamingMessages] = useState<ConversationMessage[]>([]);

    const streamingBufferRef = useRef<string[]>([])
    const flushScheduledRef = useRef<boolean>(false)

    const flushBuffer = () => {
        const joinedText = streamingBufferRef.current.join("")
        streamingBufferRef.current = []
        flushScheduledRef.current = false
        setStreamingMessages(prev => prev.map((msg, idx) => {
              if (idx === prev.length -1 && msg.type === "assistant" && msg.props.status !== "done") {
                return {
                    type: "assistant",
                    props: {
                        status: "streaming",
                        message: msg.props.status === "loading" ? joinedText : msg.props.message + joinedText
                    }
                }
              }
              return msg;
        }));
    }
    
    const streamCancellerRef = useRef<AbortController>(new AbortController());

    const { error } = useToast()


    const isAtBottomRef = useRef(true);

    // Track if the user has manually scrolled away from the bottom
    const handleScroll = useCallback(() => {
        const container = document.getElementById("messages-container")
        if (!container) return;

        const threshold = 50; // Pixels from the absolute bottom
        const distanceFromBottom =
        container.scrollHeight - container.scrollTop - container.clientHeight;

        // User is considered "at bottom" if they are within the threshold
        isAtBottomRef.current = distanceFromBottom <= threshold;
    }, []);

    const scrollToBottom = () => {
        const container = document.getElementById("messages-container")
        if (!container) return;
        container.scrollTo({
            top: container.scrollHeight,
            behavior: "auto", // Use "smooth" if you want a sliding effect
        });
    }

    // Automatically scroll to bottom when dependencies (like tokens) change
    useEffect(() => {
        const container = document.getElementById("messages-container")
        if (!container || !isAtBottomRef.current) return;
        
        const lastMessage = streamingMessages[streamingMessages.length - 1]
        if (!lastMessage) return;
        
        if (lastMessage.type === "assistant" && lastMessage.props.status === "streaming") {

            if (isAtBottomRef.current) {
                 container.scrollTo({
                    top: container.scrollHeight,
                    behavior: "auto", // Use "smooth" if you want a sliding effect
                });
            }
        }
      
    }, [streamingMessages, handleScroll]);

 

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

    useEffect(() => {

        if (isAtBottomRef.current) {
            requestAnimationFrame(() => scrollToBottom())
        }

    }, [historicalMessages])


    const allMessages = useMemo(() => {
        return [...historicalMessages, ...streamingMessages];
    }, [historicalMessages, streamingMessages]);

    // Cleanup abort controller on component unmount
    useEffect(() => {
        return () => streamCancellerRef.current.abort();
    }, []);

    const onUserPromptSubmitted = useCallback((query: string) => {

        console.count("onUserPromptSubmitted")

        streamCancellerRef.current.abort();
        streamCancellerRef.current = new AbortController();

        const started = performance.now();
        setQuery("");

        isAtBottomRef.current = true

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
                    status: "loading"
                }
            }
        ]);

        streamSse(
            {
                url: `stories/${storyId}/chat/threads/${threadId}/turn`,
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
                            streamingBufferRef.current.push(data.delta)
                            if (!flushScheduledRef.current) {
                                flushScheduledRef.current = true
                                requestAnimationFrame(flushBuffer)
                            }
                            break;
                        }
                    }
                },
                onClose: Some(() => {
                    if (streamingBufferRef.current.length > 0) flushBuffer()
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
                        console.error(`${e._tag}: Stream aborted!`)
                        return;
                    case "SseHttpError":
                        error(
                            "Error", 
                            "Something went wrong. And Nexus could not reply to your message. The server might be experiencing issues."
                        )
                        console.error(`${e._tag}: \n Status: ${e.status} \n Body: ${e.body}`);
                        return;
                    case "SseNetworkError":
                        error(
                            "Error", 
                            "Something went wrong. And Nexus could not reply to your message. The server might be experiencing issues."
                        )
                        console.error(`${e._tag}: \n ${e.cause.message}`)
                        return;
                    case "SseNoBodyError":
                        error(
                            "Error", 
                            "Something went wrong. And Nexus could not reply to your message. The server might be experiencing issues."
                        )
                        console.error(`${e._tag}: No body!`)
                        return;
                    case "SseStreamError":
                        error(
                            "Error", 
                            "Something went wrong. And Nexus could not reply to your message. The server might be experiencing issues."
                        )
                        console.error(`${e._tag}: \n ${e.cause.message}`)
                        return;
                }
            }
        });
    }, [storyId, threadId, onRetry, user, error])

    useEffect(() => {
        if (!search.prompt) return 

        const initialPrompt = search.prompt;
        
        navigate({
            search: (prev) => ({ ...prev, prompt: undefined }),
            replace: true,
        });

        // 2. Wrap the initial submission state update in a transition
        startTransition(() => {
            onUserPromptSubmitted(initialPrompt);
        });

    }, [search, onUserPromptSubmitted, navigate])

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
                onMessagesScroll: handleScroll,
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
