import { Some } from "oxide.ts";
import { LoadingSkeleton, Nothing } from "../../../../common";
import styles from "./ChapterEditorHeader.module.css"


export type ChapterEditorHeaderProps =
| { status: "loading" }
| { status: "empty" }
| { status: "error" }
| {
    status: "ready"
    saving: boolean
    chapterNumber: number
    chapterTitle: string
    wordCount: number
  }

export function ChapterEditorHeader(props: ChapterEditorHeaderProps) {
    switch (props.status) {
        case "empty":
        case "error": {
            return <Nothing />
        }
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
                        {`${props.wordCount} words - ${props.saving ? "saving..." : "saved"}`}
                    </span>
                </div>
            )
        }
    }
}