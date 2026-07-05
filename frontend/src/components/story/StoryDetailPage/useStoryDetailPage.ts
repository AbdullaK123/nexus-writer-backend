import { useEffect, useEffectEvent, useState } from "react";
import { useChapterSummary, useCreateChapter, useStoryChapters, useStoryStats } from "../../../data/queries";
import type { ChapterListProps } from "./ChapterList/ChapterList";
import type { StoryHeaderProps } from "./StoryHeader/StoryHeader";
import type { StoryOverviewProps } from "./StoryOverview/StoryOverview";
import { useNavigate, useParams } from "@tanstack/react-router"
import { Option, Some, None } from "oxide.ts"
import type { BookPulseProps } from "./BookPulse/BookPulse";
import { useStoryHeaderProps } from "./hooks/useStoryHeaderProps";
import { useStoryOverviewProps } from "./hooks/useStoryOverviewProps";
import { useChapterListProps } from "./hooks/useChapterListProps";
import { useBookPulse } from "./BookPulse/useBookPulse";
import { useToast } from "../../common";

export type StoryDetailPageProps = {
  storyHeader: StoryHeaderProps
  storyOverview: StoryOverviewProps
  chapterList: ChapterListProps
  bookPulse: BookPulseProps
}

export function useStoryDetailPage(): StoryDetailPageProps {
  const { storyId } = useParams({ from: "/app/stories/$storyId" })
  // Minimal wiring for now: keep everything in loading to satisfy DU boundaries while we derive real state next.
  const navigate = useNavigate()

  const [selectedChapterId, setSelectedChapterId] = useState<Option<string>>(None)
  const [modalOpen, setModalOpen] = useState(false)
  const [chapterTitle, setChapterTitle] = useState("")
  const [selectedFilter, setSelectedFilter] = useState<'all' | 'draft' | 'published'>('all')
  const { error, success } = useToast()

  const [storyState, refetchStory] = useStoryChapters(storyId)
  const [statsState, refetchStats] = useStoryStats(storyId)
  const [summaryState, refetchSummary] = useChapterSummary(selectedChapterId)
  const { 
    mutate: createChapter
  } = useCreateChapter(storyId)

  const onStoryError = useEffectEvent(() => {
    error("Failed to fetch story data.", "Something went wrong. The server might be experiencing issues.")
  })

  const onStatsError = useEffectEvent(() => {
    error("Failed to fetch story stats.", "Something went wrong. The server might be experiencing issues.")
  })

  const onSummaryError = useEffectEvent(() => {
    error("Failed to fetch chapterSummary.", "Something went wrong. The server might be experiencing issues.")
  })

  useEffect(() => {
    if (storyState.status === "error") onStoryError()
  }, [storyState.status])

  useEffect(() => {
    if (statsState.status === "error") onStatsError()
  }, [statsState.status])

  useEffect(() => {
    if (summaryState.status === "error") onSummaryError()
  }, [summaryState.status])

  const handleChapterCreate = () => createChapter(
    { title: chapterTitle, content: "" },
    {
      onSuccess: () => {
        success("Successfully created a new chapter!", "Happy writing!")
      },
      onError: () => {
        error("Failed to create a new chapter", "Something went wrong. The server might be experiencing issues.")
      },
      onSettled: () => {
        setChapterTitle("")
        setModalOpen(false)
      }
    }
  )

  const storyHeader: StoryHeaderProps = useStoryHeaderProps({
    chaptersState: storyState,
    chapterTitle: chapterTitle,
    onChapterTitleChange: (title: string) => setChapterTitle(title),
    modalOpen: modalOpen,
    onModalOpenChange: (open: boolean) => setModalOpen(open),
    onNavigateToLibrary: () => navigate({ to: "/" }),
    onClickSettings: () => {},
    onAskNexus: () => {},
    onNewChapter: handleChapterCreate,
    onRetry: refetchStory
  })

  const storyOverview: StoryOverviewProps = useStoryOverviewProps({
    storyState: storyState,
    summaryState: summaryState,
    statsState: statsState,
    onRetryStats: refetchStats,
    onRetrySummary: refetchSummary
  })


  const chapterList: ChapterListProps = useChapterListProps({
    chaptersState: storyState,
    selectedChapterId: selectedChapterId,
    selectedFilter: selectedFilter,
    onFilterChange: (filter: 'all' | 'draft' | 'published') => setSelectedFilter(filter),
    onRetry: refetchStory,
    onChapterClick: (chapterId: string) => setSelectedChapterId(Some(chapterId)),
    onChapterDoubleClick: (chapterId: string) => navigate({ to: `/stories/${storyId}/${chapterId}` })
  })

  const bookPulse: BookPulseProps = useBookPulse(storyId)

  return { storyHeader, storyOverview, chapterList, bookPulse }
}