import { useState } from "react"
import { useStoryPulse } from "../../../../data/queries/story"
import type { BookPulseResponse, PulseDimension } from "../../../../infrastructure/api/types"
import type { BookPulseProps } from "./BookPulse"
import { useToast } from "../../../common"
import { useCreateThread } from "../../../../data/queries";
import { useNavigate } from "@tanstack/react-router";

export function useBookPulse(storyId: string): BookPulseProps {

  const [threadCreationPending, setThreadCreationPending] = useState(false)

  const pulseState = useStoryPulse(storyId)

  const { error, info } = useToast()

  const {
    mutate: createThread
  } = useCreateThread(storyId)

  const navigate = useNavigate()

  const onDigIntoThis = (pulse: PulseDimension) => {

    if (pulse.label === "unavailable") {
      info("Nothing to investigate", "There is nothing to investigate yet. Keep writing until Nexus notices something.")
      return
    }

    const evidenceChapters = pulse.evidence_chapters.length > 0
      ? pulse.evidence_chapters.map((chapter) => `- Chapter ${chapter}`).join("\n")
      : "- No chapter evidence is available yet."
    const message = [
      "Help me investigate this story pulse finding.",
      "",
      "## Headline",
      pulse.headline,
      "",
      "## What's working",
      pulse.whats_working,
      "",
      "## What's not working",
      pulse.whats_not_working,
      "",
      "## Evidence chapters",
      evidenceChapters,
      "",
      "Verify this against the story. Explain the pattern, identify the most relevant scenes, and suggest what I should inspect next.",
    ].join("\n")

    setThreadCreationPending(true)

    createThread(
      {
        firstMessage: message
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
              prompt: message
            }
          })
        },
        onError: () => {
          setThreadCreationPending(false)
          error("Error", "Something went wrong and we could not investigate your pulse finding. The server might be experiencing issues.")
        }
      }
    )

  }

  switch (pulseState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' }
    case 'empty':
      return { status: 'empty' }
    case 'success': {
      const data: BookPulseResponse = pulseState.data.unwrap().unwrap()
      return {
        status: 'ready',
        threadCreationPending: threadCreationPending,
        onDigIntoThis: onDigIntoThis,
        characters: data.characters,
        plot: data.plot,
        structure: data.structure,
        world: data.world
      }
    }
  }
}