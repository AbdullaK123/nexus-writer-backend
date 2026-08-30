import { useSortable } from "@dnd-kit/react/sortable";
import { ChapterListItemMenu } from "../../../../story/StoryDetailPage/ChapterList/ChapterListItem/ChapterListItemMenu";
import styles from "./ChapterSidebarItem.module.css"

export type ChapterSidebarItemProps = 
| {
        status: "idle"
        index: number
        chapterId: string
        storyId: string
        chapterTitle: string
        chapterStatus: "draft" | "published"
        chapterNumber: number
        reorderDisabled?: boolean
        onClick: () => void
  }
| {
        status: "selected"
        index: number
        chapterId: string
        storyId: string
        chapterTitle: string
        chapterNumber: number
        chapterStatus: "draft" | "published"
        reorderDisabled?: boolean
        onClick: () => void
  }


const getStyles = (chapterStatus: "draft" | "published") => {
    switch (chapterStatus) {
        case "draft": return styles['draft']
        case "published": return styles['published']
    }
}


export function ChapterSidebarItem(props: ChapterSidebarItemProps) {

    const reorderDisabled = props.reorderDisabled ?? false
    const {ref, isDragging, isDropTarget} = useSortable({
        id: props.chapterId,
        index: props.index,
        disabled: reorderDisabled,
    })

    switch (props.status) {
        case "idle": {
            return (
                <div
                    ref={ref}
                    className={`${styles['content']} ${isDragging ? styles['dragging'] : ""} ${isDropTarget ? styles['drop-target'] : ""}`}
                    onClick={props.onClick}
                    aria-disabled={reorderDisabled}
                    data-reorder-disabled={reorderDisabled ? "true" : "false"}
                >
                    <span className={getStyles(props.chapterStatus)}>
                        {props.chapterNumber}
                    </span>
                    <h4 className={styles['chapter-title']}>{props.chapterTitle}</h4>
                    {(props.chapterStatus === "draft") && (
                        <div className={styles['flex-row']}>
                            <span className={getStyles(props.chapterStatus)}>
                                {props.chapterStatus}
                            </span>
                            <ChapterListItemMenu 
                                storyId={props.storyId}
                                chapterId={props.chapterId}
                                chapterStatus={props.chapterStatus}
                            />
                        </div>
                    )}
                </div>
            )
        }
        case "selected": {
            return (
                <div
                    ref={ref}
                    className={`${styles['content']} ${isDragging ? styles['dragging'] : ""} ${isDropTarget ? styles['drop-target'] : ""} ${styles['selected']}`}
                    onClick={props.onClick}
                    aria-disabled={reorderDisabled}
                    data-reorder-disabled={reorderDisabled ? "true" : "false"}
                >
                    <span className={styles['editing']}>
                        {props.chapterNumber}
                    </span>
                    <h4 className={styles['chapter-title']}>{props.chapterTitle}</h4>
                    <div className={styles['flex-row']}>
                        <span className={styles['editing']}>
                            editing
                        </span>
                         <ChapterListItemMenu 
                            storyId={props.storyId}
                            chapterId={props.chapterId}
                            chapterStatus={props.chapterStatus}
                        />
                    </div>
                </div>
            )
        }
    }
} 