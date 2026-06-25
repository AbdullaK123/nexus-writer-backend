import { formatDistanceToNow } from "date-fns"
import styles from "./ChapterListItem.module.css"

export type ChapterListItemProps = {
    chapterNumber: number 
    chapterTitle: string 
    chapterStatus: "draft" | "published"
    updatedAt: Date
    wordCount: number
    selected: boolean,
    onClick: () => void
    onDoubleClick: () => void
}

export function ChapterListItem({
    chapterNumber,
    chapterTitle,
    chapterStatus,
    updatedAt,
    wordCount,
    selected,
    onClick,
    onDoubleClick
}: ChapterListItemProps) {
    return (
        <div
            className={`${styles['content']} ${selected ? styles['selected'] : ""}` }
            onClick={onClick}
            onDoubleClick={onDoubleClick}
        >
            <div className={styles['chapter-info-container']}>
                <p className={styles['chapter-number']}>{chapterNumber}</p>
                <div className={styles['chapter-info']}>
                    <h4>{chapterTitle}</h4>
                    <p className={chapterStatus === "draft" ? `${styles['draft']} ${styles['all-caps']}` : styles['all-caps']}>
                        {chapterStatus === "draft" ? "DRAFT" : `EDITED ${formatDistanceToNow(updatedAt, { addSuffix: true })}`}
                    </p>
                </div>
            </div>
            <div className={styles['all-caps']}>
                <p>{`${wordCount} WORDS`}</p>
            </div>
        </div>
    )
}