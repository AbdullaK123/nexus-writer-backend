import { None } from "oxide.ts";
import { useStoryChapters } from "../../../data/queries";
import type { ChapterListProps } from "./ChapterList/ChapterList";
import type { StoryHeaderProps } from "./StoryHeader/StoryHeader";
import type { StoryOverviewProps } from "./StoryOverview/StoryOverview";
import type { BookPulseProps } from "./BookPulse/BookPulse";
import { useBookPulse } from "./BookPulse/useBookPulse";
import { useNavigate, useSearch } from "@tanstack/react-router";
import { useStoryHeaderProps } from "./hooks/useStoryHeaderProps";
import { useChapterListProps } from "./hooks/useChapterListProps";
import { useStoryOverview } from "./StoryOverview/useStoryOverview";

export type StoryDetailPageProps = {
  storyHeader: StoryHeaderProps
  storyOverview: StoryOverviewProps
  bookPulse: BookPulseProps
  chapterList: ChapterListProps
}

export function useStoryDetailPage(): StoryDetailPageProps {
  const { storyId } = useSearch({ from: "/app/stories/$storyId" });
  const navigate = useNavigate();
  const [chaptersState, refetchChapters] = useStoryChapters(storyId);

  const storyHeader: StoryHeaderProps = useStoryHeaderProps({
    chaptersState,
    onRetry: () => { void refetchChapters(); },
    onNavigateToLibrary: () => navigate({ to: "/" }),
    onClickSettings: () => {},
    onAskNexus: () => {},
    onNewChapter: () => {},
  });

  // Keep StoryOverview using its own subhook; pass Nones to yield 'loading' until details are wired.
  const storyOverview: StoryOverviewProps = useStoryOverview({
    storyId,
    storyStatus: None,
    createdAt: None,
    storyTitle: None,
    selectedChapterId: "",
  });

  const bookPulse: BookPulseProps = useBookPulse(storyId);

  const chapterList: ChapterListProps = useChapterListProps({
    chaptersState,
    onRetry: () => { void refetchChapters(); }
  });

  return { storyHeader, storyOverview, bookPulse, chapterList };
}