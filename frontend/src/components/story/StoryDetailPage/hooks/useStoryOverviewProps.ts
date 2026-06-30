import { formatDistanceToNow } from "date-fns";
import type { AsyncState, ChapterListResponse, ChapterSummaryResponse, StoryStatsResponse } from "../../../../infrastructure/api/types";
import type { ApiError } from "../../../../shared/types";
import { toStatusBadgeVariant } from "../../DashboardPage/LibraryGrid/StoryCard";
import type { StoryOverviewProps } from "../StoryOverview/StoryOverview";
import { resolveAsyncStates } from "../../../../infrastructure/api/utils";



export type UseStoryOverviewArgs = {
    storyState: AsyncState<ChapterListResponse, ApiError>,
    summaryState: AsyncState<ChapterSummaryResponse, ApiError>,
    statsState: AsyncState<StoryStatsResponse, ApiError>,
    onRetryStats: () => void;
    onRetrySummary: () => void;
}

export function useStoryOverviewProps({
    storyState,
    summaryState,
    statsState,
    onRetryStats,
    onRetrySummary
}: UseStoryOverviewArgs): StoryOverviewProps {


    console.log(JSON.stringify({storyState, summaryState, statsState}, null, 2))
    const resolvedState = resolveAsyncStates({
        story: storyState,
        summary: summaryState,
        stats: statsState
    })
    
    switch (resolvedState.status) {
        case "loading":
            return {
                status: "loading"
            }
        case "error":
            return {
                status: "error",
                headline: "Error",
                title: "Failed to fetch story info",
                description: "Something went wrong. The server might be experiencing issues.",
                onRetryStats: onRetryStats,
                onRetrySummary: onRetrySummary
            }
        case "empty":
            return {
                status: "empty",
                badge: toStatusBadgeVariant("Ongoing"),
                startedText: "N/A",
                titleText: "N/A"
            }
        case "success":
            return {
                status: "ready",
                badge: toStatusBadgeVariant(resolvedState.data.story.storyStatus),
                startedText: `STARTED ${formatDistanceToNow(resolvedState.data.story.storyLastUpdated, { addSuffix: true })}`,
                titleText: resolvedState.data.story.storyTitle,
                summaryText: resolvedState.data?.summary?.summary,
                stats: resolvedState.data.stats
            }
    }


}