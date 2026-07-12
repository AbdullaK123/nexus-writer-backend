import { useState } from "react";
import type { AsyncState, ChatMessageListResponse, StoryDetailResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import type { StoryChatHeaderProps } from "./StoryChatHeader";
import { useToast } from "../../../common";
import { useDeleteThread, useRenameThread } from "../../../../data/queries";
import { resolveAsyncStates } from "../../../../infrastructure/api/utils";

export type UseStoryChatHeaderPropsArgs = 
{
    storyId: string
    threadId: string
    conversationState: AsyncState<ChatMessageListResponse, ApiError>
    storyState: AsyncState<StoryDetailResponse, ApiError>
}

export function useStoryChatHeaderProps({
    storyId,
    threadId,
    conversationState,
    storyState
}: UseStoryChatHeaderPropsArgs): StoryChatHeaderProps {

    const resolvedState = resolveAsyncStates({
        conversation: conversationState,
        story: storyState
    })

    const [newThreadTitle, setNewThreadTitle] = useState("")
    const [renameModalOpen, setRenameModalOpen] = useState(false)
    const [deleteModalOpen, setDeleteModalOpen] = useState(false)

    const { success, error } = useToast()

    const {
        mutate: renameThread 
    } = useRenameThread(storyId, threadId)

    const {
        mutate: deleteThread
    } = useDeleteThread(storyId, threadId)


    const onRename = () => {
        renameThread(
            {
                title: newThreadTitle
            },
            {
                onSuccess: () => {
                    success("Succesfully renamed thread!", "")
                },
                onError: () => {
                    error("Error!", "Something went wrong. The server might be experiencing issues.")
                },
                onSettled: () => {
                    setNewThreadTitle("")
                    setRenameModalOpen(false)
                }
            }
        )
    }

    const onDelete = () => {
        deleteThread(undefined,
            {
                onSuccess: () => {
                    success("Succesfully deleted thread!", "")
                },
                onError: () => {
                    error("Error!", "Something went wrong. The server might be experiencing issues.")
                },
                onSettled: () => {
                    setDeleteModalOpen(false)
                }
            }
        )
    }
    
    switch (resolvedState.status) {
        case "empty": {
            return { status: "empty" }
        }
        case "error": {
            return { status: "error" }
        }
        case "idle": {
            return { status: "idle"}
        }
        case "loading": {
            return { status: "loading" }
        }
        case "success": {

            const data = resolvedState.data

            return {
                status: "ready",
                storyTitle: data.story.title,
                threadTitle: data.conversation.threadTitle,
                newThreadTitle: newThreadTitle,
                onNewThreadTitleChange: (query: string) => setNewThreadTitle(query),
                renameModalOpen: renameModalOpen,
                onRenameModalOpenChange: (e: boolean) => setRenameModalOpen(e),
                deleteModalOpen: deleteModalOpen,
                onDeleteModalOpenChange: (e: boolean) => setDeleteModalOpen(e),
                onRename: onRename,
                onDelete: onDelete,
                onExport: () => {}
            }
        }
    }
}