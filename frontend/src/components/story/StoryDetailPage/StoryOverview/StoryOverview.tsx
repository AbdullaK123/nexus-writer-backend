import { useChapterSummary } from "../../../../data/queries";
import type { StoryStatus } from "../../../../infrastructure/api/types";
import { Button, StatusBadge, useToast } from "../../../common";
import { formatDistanceToNow } from "date-fns"
import styles from "./StoryOverview.module.css"
import { useEffect, useEffectEvent } from "react";


export type StoryOverviewProps = {
    storyStatus: StoryStatus,
    createdAt: Date,
    storyTitle: string,
    selectedChapterId: string,
    totalChapters: number
    totalWords: number
    totalScenes: number
    currentStreak: number
}

export function StoryOverview({
    storyStatus,
    createdAt,
    storyTitle,
    selectedChapterId,
    totalChapters,
    totalWords,
    totalScenes,
    currentStreak
}: StoryOverviewProps) {

    const [summaryState, refetchSummary] = useChapterSummary(selectedChapterId)

    const { error } = useToast()

    const onFetchFailed = useEffectEvent(() => {
        error("Failed to fetch chapter summary", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (summaryState.status === "error") onFetchFailed()
    }, [summaryState.status])

    const toStatusVariant = (status: StoryStatus) => {
        switch (status) {
            case "Complete": return "complete"
            case "On Hiatus": return "hiatus"
            case "Ongoing": return "ongoing"
            default: return "ongoing"
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
            <div className={styles['stats-container']}>
                <div className={styles['stat']}>
                    <p className={styles['all-caps']}>Chapters</p>
                    <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{totalChapters}</p>
                </div>
                <div className={styles['stat']}>
                    <p className={styles['all-caps']}>Words</p>
                    <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{totalWords}</p>
                </div>  
                <div className={styles['stat']}>
                    <p className={styles['all-caps']}>Scenes</p>
                    <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{totalScenes}</p>
                </div>
                <div className={styles['stat']}>
                    <p className={styles['all-caps']}>Streak</p>
                    <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{currentStreak}</p>
                </div>
            </div>
        </div>
    )
}   