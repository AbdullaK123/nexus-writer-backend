import type { ChapterListProps } from "../ChapterList/ChapterList";
import type { AsyncState, ChapterListResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";

export function useChapterListProps(args: {
  chaptersState: AsyncState<ChapterListResponse, ApiError>
  onRetry: () => void
}): ChapterListProps {
  const { chaptersState, onRetry } = args;
  switch (chaptersState.status) {
    case 'idle':
    case 'loading':
      return { status: 'loading' };
    case 'error':
      return { status: 'error', headline: 'Chapters Error', title: 'Failed to load chapters', onRetry };
    case 'empty':
      return {
        status: 'empty',
        filterBar: {
          status: 'ready',
          totalChapters: 0,
          totalDraftChapters: 0,
          totalPublishedChapters: 0,
          selected: 'all',
          onClickFilterChip: () => {}
        }
      };
    case 'success': {
      // Minimal first pass: treat success with data as ready with a static filter bar and an empty list until the full derivation is implemented.
      return {
        status: 'ready',
        filterBar: {
          status: 'ready',
          totalChapters: 0,
          totalDraftChapters: 0,
          totalPublishedChapters: 0,
          selected: 'all',
          onClickFilterChip: () => {}
        },
        items: []
      };
    }
  }
}
