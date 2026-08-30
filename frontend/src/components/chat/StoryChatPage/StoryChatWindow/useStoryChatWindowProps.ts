import { useState, useEffect, useRef, useCallback, useMemo, startTransition } from "react";
import type { AsyncState, ChatMessageListResponse, UserResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatWindowProps, ConversationMessage } from "./StoryChatWindow";
import { streamSse } from "../../../../infrastructure/sse";
import { beginChatTurn, buildChatTurnRequest, completeChatTurn, decodeChatStreamToken, finishChatTurn } from "../../../../infrastructure/chat-stream";
import { SingleFlightGate } from "../../../../shared/singleFlight";
import { AbortControllerSlot } from "../../../../shared/abortControllerSlot";
import { Some, Option } from "oxide.ts";
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
    const [threadCreationPending, setThreadCreationPending] = useState(false)
    const turnGateRef = useRef(new SingleFlightGate())
    const streamSlotRef = useRef(new AbortControllerSlot())
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

    const { error } = useToast()
    const isAtBottomRef = useRef(true);

    const handleScroll = useCallback(() => {
        const container = document.getElementById("messages-container")
        if (!container) return;
        const threshold = 50;
        const distanceFromBottom = container.scrollHeight - container.scrollTop - container.clientHeight;
        isAtBottomRef.current = distanceFromBottom <= threshold;
    }, []);

    const scrollToBottom = () => {
        const container = document.getElementById("messages-container")
        if (!container) return;
        container.scrollTo({ top: container.scrollHeight, behavior: "auto" });
    }

    useEffect(() => {
        const container = document.getElementById("messages-container")
        if (!container || !isAtBottomRef.current) return;
        const lastMessage = streamingMessages[streamingMessages.length - 1]
        if (!lastMessage) return;
        if (lastMessage.type === "assistant" && lastMessage.props.status === "streaming") {
            container.scrollTo({ top: container.scrollHeight, behavior: "auto" });
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
                                    user,
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
                                props: { status: "done", message: part.content as string }
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
        if (isAtBottomRef.current) requestAnimationFrame(() => scrollToBottom())
    }, [historicalMessages])

    const allMessages = useMemo(() => [...historicalMessages, ...streamingMessages], [historicalMessages, streamingMessages]);

    useEffect(() => {
        return () => {
            // eslint-disable-next-line react-hooks/exhaustive-deps
            streamSlotRef.current.abort();
            // eslint-disable-next-line react-hooks/exhaustive-deps
            finishChatTurn(turnGateRef.current);
        }
    }, []);

    const finishTurn = () => {
        finishChatTurn(turnGateRef.current)
        setThreadCreationPending(false)
    }

    const onUserPromptSubmitted = useCallback((query: string) => {
        const controller = beginChatTurn(turnGateRef.current, streamSlotRef.current)
        if (!controller) return
        setThreadCreationPending(true)

        const started = performance.now();
        setQuery("");
        isAtBottomRef.current = true
        setStreamingMessages([
            { type: "user", props: { user, createdAt: new Date(), message: query } },
            { type: "assistant", props: { status: "loading" } }
        ]);

        streamSse(
            buildChatTurnRequest(storyId, threadId, query, controller.signal),
            {
                onEvent: (event: EventSourceMessage) => {
                    const delta = decodeChatStreamToken(event)
                    if (delta === null) return
                    streamingBufferRef.current.push(delta)
                    if (!flushScheduledRef.current) {
                        flushScheduledRef.current = true
                        requestAnimationFrame(flushBuffer)
                    }
                },
                onClose: Some(() => {
                    if (streamingBufferRef.current.length > 0) flushBuffer()
                    setStreamingMessages([]);
                    finishTurn()
                    completeChatTurn(onRetry)
                })
            }
        ).then((result) => {
            console.log(`SSE stream finished in ${((performance.now() - started) / 1000).toFixed(2)}s`);
            if (result.isOk()) return

            const e = result.unwrapErr();
            if (e._tag === "SseAbortedError") {
                finishTurn()
                return;
            }

            error(
                "Error", 
                "Something went wrong. And Nexus could not reply to your message. The server might be experiencing issues."
            )
            if (streamingBufferRef.current.length > 0) flushBuffer()
            setStreamingMessages([]);
            onRetry()
            finishTurn()
        });
    }, [storyId, threadId, onRetry, user, error])

    useEffect(() => {
        if (!search.prompt) return 
        const initialPrompt = search.prompt;
        navigate({ search: (prev) => ({ ...prev, prompt: undefined }), replace: true });
        startTransition(() => onUserPromptSubmitted(initialPrompt));
    }, [search, onUserPromptSubmitted, navigate])

    switch (conversationState.status) {
        case "loading": return { status: "loading" }
        case "empty": return {
            status: "empty",
            composer: {
                status: "ready",
                threadCreationPending,
                query,
                onQueryChange: setQuery,
                onEnterDown: onUserPromptSubmitted,
                onSubmit: onUserPromptSubmitted
            }
        };
        case "idle": return { status: "empty", composer: { status: "empty" } };
        case "success": return {
            status: "ready",
            messages: allMessages, 
            onMessagesScroll: handleScroll,
            composer: {
                status: streamingMessages.length > 0 ? "loading" : "ready",
                query,
                threadCreationPending,
                onQueryChange: setQuery,
                onEnterDown: onUserPromptSubmitted,
                onSubmit: onUserPromptSubmitted
            }
        };
        default: return { status: "empty", composer: { status: "empty" } };
    }
}
