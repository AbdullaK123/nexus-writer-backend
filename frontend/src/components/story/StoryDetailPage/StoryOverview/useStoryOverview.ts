import { formatDistanceToNow } from 'date-fns'
import { useEffect, useEffectEvent } from 'react'
import { Option } from 'oxide.ts'
import type { StoryStatus } from '../../../../infrastructure/api/types'
import { useChapterSummary } from '../../../../data/queries/chapter'
import { useStoryStats } from '../../../../data/queries/story'
import type { StoryOverviewProps } from './StoryOverview'
import { useToast } from '../../../common'
import { toStatusBadgeVariant } from '../../DashboardPage/LibraryGrid/StoryCard/utils'

export type UseStoryOverviewArgs = {
  storyId: string
  storyStatus: Option<StoryStatus>
  createdAt: Option<Date>
  storyTitle: Option<string>
  selectedChapterId: string
}

export function useStoryOverview(args: UseStoryOverviewArgs): StoryOverviewProps {
  const { storyId, storyStatus, createdAt, storyTitle, selectedChapterId } = args

  const [summaryState, refetchSummary] = useChapterSummary(selectedChapterId)
  const [statsState, refetchStats] = useStoryStats(storyId)

  const { error } = useToast()

  const onSummaryFetchFailed = useEffectEvent(() => {
    error('Failed to fetch chapter summary', 'Something went wrong. The server might be experiencing issues.')
  })
  const onStatsFetchFailed = useEffectEvent(() => {
    error('Failed to fetch story stats', 'Something went wrong. The server might be experiencing issues.')
  })

  useEffect(() => {
    if (summaryState.status === 'error') onSummaryFetchFailed()
  }, [summaryState.status])

  useEffect(() => {
    if (statsState.status === 'error') onStatsFetchFailed()
  }, [statsState.status])

  // While required metadata is missing, treat as loading to avoid illegal states.
  if (storyStatus.isNone() || createdAt.isNone() || storyTitle.isNone()) {
    return { status: 'loading' }
  }

  const badge = toStatusBadgeVariant(storyStatus.unwrap())
  const startedText = `Started ${formatDistanceToNow(createdAt.unwrap(), { addSuffix: true })}`
  const titleText = storyTitle.unwrap()

  // Any loading/idle state → loading
  if (summaryState.status === 'idle' || summaryState.status === 'loading' || statsState.status === 'idle' || statsState.status === 'loading') {
    return { status: 'loading' }
  }

  // Any error → error with retry
  if (summaryState.status === 'error' || statsState.status === 'error') {
    return {
      status: 'error',
      headline: 'Overview Error',
      title: 'Failed to load story overview',
      description: 'One or more requests failed. Please try again.',
      onRetryStats: () => refetchStats(),
      onRetrySummary: () => refetchSummary(),
    }
  }

  // Empty summary case
  if (summaryState.status === 'empty') {
    return {
      status: 'empty',
      badge,
      startedText,
      titleText,
    }
  }

  // Success case requires both
  if (summaryState.status === 'success' && statsState.status === 'success') {
    const s = statsState.data.unwrap().unwrap()
    const summaryText = summaryState.data.unwrap().unwrap().summary
    return {
      status: 'ready',
      badge,
      startedText,
      titleText,
      summaryText,
      stats: {
        totalChapters: s.totalChapters,
        totalWords: s.totalWords,
        totalScenes: s.totalScenes,
        streakDays: s.streakDays,
      },
    }
  }

  // Stats might be empty (unlikely) → empty with zeros
  if (statsState.status === 'empty') {
    return {
      status: 'empty',
      badge,
      startedText,
      titleText,
    }
  }

  // Fallback
  return { status: 'loading' }
}
