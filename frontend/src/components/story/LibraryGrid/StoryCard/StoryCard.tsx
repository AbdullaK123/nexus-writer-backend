import type { StoryStatus } from "../../../../infrastructure/api/types";
import { formatDistanceToNowStrict  } from 'date-fns'
import { Card, StatusBadge } from "../../../common"
import styles from "./StoryCard.module.css"
import { toStatusBadgeVariant } from "./utils";


export type StoryCardProps = {
    storyId: string 
    status: StoryStatus
    chapterNumber: number
    title: string
    wordCount: number
    updatedAt: Date
    onClick: (storyId: string) => void;
}



export function StoryCard({
    storyId,
    status,
    chapterNumber,
    title,
    wordCount,
    updatedAt,
    onClick
}: StoryCardProps)  {
    return (
        <Card
            onClick={() => onClick(storyId)}
            header={(
                <div className={styles['header-container']}>
                    <StatusBadge variant={toStatusBadgeVariant(status)} />
                    <p className={styles['all-caps']}>{`${chapterNumber} CH`}</p>
                </div>
            )}
            footer={(
                <div className={styles['footer-container']}>
                    <p className={styles['color-cyan']}>{wordCount}</p>
                    <p className={styles['all-caps']}>{formatDistanceToNowStrict(updatedAt, { addSuffix: true })}</p>
                </div>
            )}
        >
            {title}
        </Card>
    )
}
