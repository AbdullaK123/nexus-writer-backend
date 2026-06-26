import type { StoryHeaderProps } from "../StoryHeader/StoryHeader";
import type { AsyncState, ChapterListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";

export function useStoryHeaderProps(args: {
  chaptersState: AsyncState<ChapterListResponse, ApiError>
  onNavigateToLibrary: () => void
  onClickSettings: () => void
  onAskNexus: () => void
  onNewChapter: () => void
  onRetry: () => void
}): StoryHeaderProps {
  const { chaptersState, onNavigateToLibrary, onClickSettings, onAskNexus, onNewChapter, onRetry } = args;
  switch (chaptersState.status) {
    case 'error':
      return {
        status: 'error',
        message: 'Failed to load story header',
        onRetry,
        onNavigateToLibrary,
        onClickSettings,
        onAskNexus,
        onNewChapter,
      }
    default:
      return {
        status: 'loading',
        onNavigateToLibrary,
        onClickSettings,
        onAskNexus,
        onNewChapter,
      }
  }
}
