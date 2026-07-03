import { None, Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../../../common";
import styles from "./ChapterEditorContentLoadingSkeleton.module.css"



export function ParagraphSkeleton() {
    return (
        <div className={styles['paragraph']}>
            <LoadingSkeleton className={Some(styles['first-line'])} />
            <LoadingSkeleton className={None} />
            <LoadingSkeleton className={None} />
            <LoadingSkeleton className={None} />
            <LoadingSkeleton className={None} />
        </div>
    )
}

export function ChapterEditorContentLoadingSkeleton() {
    return (
        <div className={styles['paragraphs-container']}>
            <ParagraphSkeleton />
            <ParagraphSkeleton />
            <ParagraphSkeleton />
        </div>
    )
}