import { useChapterSummary, useStoryStats } from "../../../../data/queries";
import type { AsyncState, StoryStatsResponse, StoryStatus } from "../../../../infrastructure/api/types";
import { Button, ErrorState, LoadingSkeleton, StatusBadge, useToast } from "../../../common";
import { formatDistanceToNow } from "date-fns"
import styles from "./StoryOverview.module.css"
import { useEffect, useEffectEvent } from "react";
import { None, Some, Option } from "oxide.ts";
import type { ApiError } from "../../../../shared/types";


export type StoryOverviewProps = {
    storyId: string
    storyStatus: Option<StoryStatus>,
    createdAt: Option<Date>,
    storyTitle: Option<string>,
    selectedChapterId: string
}

export function StoryOverview({
    storyId,
    storyStatus,
    createdAt,
    storyTitle,
    selectedChapterId
}: StoryOverviewProps) {

    const [summaryState, refetchSummary] = useChapterSummary(selectedChapterId)

    const [statsState, refetchStats] = useStoryStats(storyId)

    const { error } = useToast()

    const onSummaryFetchFailed = useEffectEvent(() => {
        error("Failed to fetch chapter summary", "Something went wrong. The server might be experiencing issues.")
    })

     const onStatsFetchFailed = useEffectEvent(() => {
        error("Failed to story stats", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (summaryState.status === "error") onSummaryFetchFailed()
    }, [summaryState.status])

     useEffect(() => {
        if (statsState.status === "error") onStatsFetchFailed()
    }, [statsState.status])

    const toStatusVariant = (status: StoryStatus) => {
        switch (status) {
            case "Complete": return "complete"
            case "On Hiatus": return "hiatus"
            case "Ongoing": return "ongoing"
            default: return "ongoing"
        }
    }

    const getStatsState = (
        state: AsyncState<StoryStatsResponse, ApiError>
    ) => {
        switch (state.status) {
            case "idle": 
                return (
                    <div className={styles['stats-container']}>
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                    </div>
                )
            case "loading": 
                return (
                    <div className={styles['stats-container']}>
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                    </div>
                )
            case "empty": 
                return (
                    <div className={styles['stats-container']}>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Chapters</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
                        </div>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Words</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
                        </div>  
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Scenes</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
                        </div>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Streak</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
                        </div>
                    </div>
                )
            case "error": 
                return (
                    <ErrorState 
                        headline="Stats Error"
                        title="Failed to fetch story stats"
                        description={Some("Something went wrong. The server might be experiencing issues")}
                        action={
                            Some(<Button
                                variant="primary"
                                onClick={() => refetchStats()}
                            >
                                Retry
                            </Button>)
                        }
                    />
                )
            case "success": 
                return (
                    <div className={styles['stats-container']}>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Chapters</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>
                                {state.data.unwrap().unwrap().totalChapters}
                            </p>
                        </div>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Words</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>
                                {state.data.unwrap().unwrap().totalWords}
                            </p>
                        </div>  
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Scenes</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>
                                {state.data.unwrap().unwrap().totalScenes}
                            </p>
                        </div>
                        <div className={styles['stat']}>
                            <p className={styles['all-caps']}>Streak</p>
                            <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>
                                {state.data.unwrap().unwrap().streakDays}
                            </p>
                        </div>
                    </div>
                )
        }
    }

    return (
        <div className={styles['overview-container']}>
            <div className={styles['details-container']}>
                <div className={styles['details-header']}>
                    <StatusBadge 
                        variant={toStatusVariant(storyStatus)}
                    />
                    <p className={styles['all-caps']}>{`Started ${formatDistanceToNow(createdAt, { addSuffix: true })}`}</p>
                </div>
                <div className={styles['summary-container']}>
                    <h2>{storyTitle}</h2>
                    {summaryState.status === "loading" && (<p>Loading summary...</p>)}
                    {summaryState.status === "error" && (
                        <div className={styles['error-state']}>
                            <p>X Failed to load chapter summary</p>
                            <Button
                                variant="primary"
                                onClick={() => refetchSummary()}
                            >
                                Retry
                            </Button>
                        </div>
                    )}
                    <p className={styles['summary']}>
                        {(summaryState.status === "success") && 
                            summaryState.data.unwrap().unwrap().summary}
                        {(summaryState.status === "empty") && "No summary yet"}
                    </p>
                </div>
            </div>
           {getStatsState(statsState)}
        </div>
    )
}   