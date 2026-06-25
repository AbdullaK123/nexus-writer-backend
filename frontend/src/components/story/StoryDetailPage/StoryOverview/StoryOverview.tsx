import { useChapterSummary } from "../../../../data/queries";
import type { StoryStatus } from "../../../../infrastructure/api/types";
import { StatusBadge, useToast } from "../../../common";
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

    const {
        data: chapterSummary,
        isLoading,
        isError
    } = useChapterSummary(selectedChapterId)

    const { error } = useToast()

    const onFetchFailed = useEffectEvent(() => {
        error("Failed to fetch chapter summary", "Something went wrong. The server might be experiencing issues.")
    })

    useEffect(() => {
        if (isError) onFetchFailed()
    }, [isError])

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
                    {isLoading && (<p>Loading summary...</p>)}
                    {isError && (<p>X Failed to load chapter summary</p>)}
                    <p className={styles['summary']}>{chapterSummary ? chapterSummary.summary : "No summary yet"}</p>
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