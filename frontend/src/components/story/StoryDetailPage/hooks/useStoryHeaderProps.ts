import type { StoryHeaderProps } from "../StoryHeader/StoryHeader";
import type { AsyncState, ChapterListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";

export function useStoryHeaderProps(args: {
  chaptersState: AsyncState<ChapterListResponse, ApiError>,
  chapterTitle: string,
  onChapterTitleChange: (title: string) => void,
  modalOpen: boolean,
  onModalOpenChange: (open: boolean) => void,
  onNavigateToLibrary: () => void,
  onClickSettings: () => void,
  onAskNexus: () => void,
  onNewChapter: () => void,
  onRetry: () => void
}): StoryHeaderProps {

  const { 
    chaptersState, 
    chapterTitle,
    onChapterTitleChange,
    modalOpen,
    onModalOpenChange,
    onNavigateToLibrary, 
    onClickSettings, 
    onAskNexus, 
    onNewChapter, 
    onRetry
   } = args;



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
    case "idle":
    case "loading":
      return {
        status: 'loading',
        chapterTitle: chapterTitle,
        modalOpen: modalOpen,
        onModalOpenChange: onModalOpenChange,
        onChapterTitleChange: onChapterTitleChange,
        onNavigateToLibrary,
        onClickSettings,
        onAskNexus,
        onNewChapter,
      }
    case "empty":
      return {
        status: "empty",
        onNavigateToLibrary,
        onClickSettings,
        onAskNexus,
        onNewChapter,
      }
    case "success":
      return {
        status: 'ready',
        title: chaptersState.data.unwrap().unwrap().storyTitle,
        chapterTitle,
        modalOpen: modalOpen,
        onModalOpenChange: onModalOpenChange,
        onChapterTitleChange: onChapterTitleChange,
        onNavigateToLibrary,
        onClickSettings,
        onAskNexus,
        onNewChapter,
      }
  }
}
