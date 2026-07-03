import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../../common";
import styles from "./ChapterEditorHeader.module.css"


export type ChapterEditorHeaderProps =
| {
    status: "loading"
  }
| {
    status: "ready"
    chapterNumber: number
    chapterTitle: string
    wordCount: number
  }
| {
    status: "saving"
    chapterNumber: number
    chapterTitle: string
    wordCount: number
  }

export function ChapterEditorHeader(props: ChapterEditorHeaderProps) {
    switch (props.status) {
        case "loading": {
            return (
                <div className={styles['content']}>
                    <LoadingSkeleton className={Some(styles['loading-pill'])} />
                    <LoadingSkeleton className={Some(styles['loading-pill'])} />
                </div>
            )
        }
        case "ready": {
            return (
                <div className={styles['content']}>
                    <span className={styles['pill']}>
                        {`CH ${props.chapterNumber} - ${props.chapterTitle}`}
                    </span>
                    <span className={styles['pill']}>
                        {`${props.wordCount} words - saved`}
                    </span>
                </div>
            )
        }
        case "saving": {
            return (
                <div className={styles['content']}>
                     <span className={styles['pill']}>
                        {`CH ${props.chapterNumber} - ${props.chapterTitle}`}
                    </span>
                    <span className={styles['pill']}>
                        {`${props.wordCount} words - saving...`}
                    </span>
                </div>
            )
        }
    }
}