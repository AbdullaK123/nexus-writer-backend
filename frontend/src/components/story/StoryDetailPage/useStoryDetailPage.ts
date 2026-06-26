import { useState } from "react";
import { useStoryChapters } from "../../../data/queries";
import type { ChapterListProps } from "./ChapterList/ChapterList";
import type { StoryHeaderProps } from "./StoryHeader/StoryHeader";
import type { StoryOverviewProps } from "./StoryOverview/StoryOverview";
import type { BookPulseProps } from "./BookPulse/BookPulse";
import { useBookPulse } from "./BookPulse/useBookPulse";
import { useNavigate, useSearch } from "@tanstack/react-router"

export type StoryDetailPageProps = {
  storyHeader: StoryHeaderProps
  storyOverview: StoryOverviewProps
  bookPulse: BookPulseProps
  chapterList: ChapterListProps
}

export function useStoryDetailPage(): StoryDetailPageProps {
  const { storyId } = useSearch({ from: "/app/stories/$storyId" })
  // Minimal wiring for now: keep everything in loading to satisfy DU boundaries while we derive real state next.
  const navigate = useNavigate()
  const [_storyChaptersState] = useStoryChapters(storyId)
  const [_modalOpen, _setModalOpen] = useState(false)

  const storyHeader: StoryHeaderProps = {
    status: 'loading',
    onNavigateToLibrary: () => navigate({ to: "/" }),
    onClickSettings: () => {},
    onAskNexus: () => {},
    onNewChapter: () => {},
  }

  const storyOverview: StoryOverviewProps = { status: 'loading' }

  const bookPulse: BookPulseProps = useBookPulse(storyId)

  const chapterList: ChapterListProps = { status: 'loading' }

  return { storyHeader, storyOverview, bookPulse, chapterList }
}