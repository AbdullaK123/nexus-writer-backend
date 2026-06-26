import { useEffect, useEffectEvent } from "react"
import { useStoryPulse } from "../../../../data/queries/story"
import type { BookPulseResponse } from "../../../../infrastructure/api/types"
import type { BookPulseProps } from "./BookPulse"
import { useToast } from "../../../common"

export function useBookPulse(storyId: string): BookPulseProps {
  const [pulseState, refetch] = useStoryPulse(storyId)
  const { error } = useToast()

  const onError = useEffectEvent(() => {
    error("Failed to load book pulse.", "Something went wrong. The server might be experiencing issues.")
  })

  useEffect(() => {
    if (pulseState.status === 'error') onError()
  }, [pulseState.status])

  switch (pulseState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' }
    case 'error':
      return { status: 'error', onRetry: () => { void refetch() } }
    case 'empty':
      return { status: 'empty' }
    case 'success': {
      const data: BookPulseResponse = pulseState.data.unwrap().unwrap()
      return {
        status: 'ready',
        characters: data.characters,
        plot: data.plot,
        structure: data.structure,
        world: data.world,
      }
    }
  }
}