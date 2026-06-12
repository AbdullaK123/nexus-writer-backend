import { formatDistanceToNowStrict } from 'date-fns'
import { Button } from '../../../common';
import styles from "./ChapterCard.module.css"

export type ChapterCardProps = {
    storyId: string 
    chapterId: string 
    chapterNumber: number 
    wordCount: number 
    storyTitle: string 
    chapterTitle: string 
    published: boolean
    updatedAt: Date
    onClick: (chapterId: string, storyId: string) => void
}


export function ChapterCard({
    storyId,
    chapterId,
    chapterNumber,
    wordCount,
    storyTitle,
    chapterTitle,
    published,
    updatedAt,
    onClick
}: ChapterCardProps) {
    return (
        <div className={styles['chapter-card']}>
            <div className={styles['chapter-card__header']}>   
                <span className={styles['chapter-card__number']}>{`CH 0${chapterNumber}`}</span>
                <p>{`${wordCount} words`}</p>
            </div>
            <div className={styles['chapter-card__content']}>
                <p>{storyTitle}</p>
                <h3>{chapterTitle}</h3>
            </div>
            <div className={styles['chapter-card__footer']}>
                <p className={`${styles['chapter-card__text']} ${published ? "" : styles['color-warning']}`}>
                    {
                        published ?
                        `edited ${formatDistanceToNowStrict(updatedAt, { addSuffix: true })}`
                        : `draft - ${formatDistanceToNowStrict(updatedAt, { addSuffix: true })}`
                    }
                </p>
                <Button
                    className={styles['color-cyan']}
                    variant="ghost"
                    onClick={() => onClick(chapterId, storyId)}
                >
                    →
                </Button>
            </div>
        </div>
    )
}