import { ChapterListItemMenu } from "../../../../story/StoryDetailPage/ChapterList/ChapterListItem/ChapterListItemMenu";
import styles from "./ChapterSidebarItem.module.css"

export type ChapterSidebarItemProps = 
| {
        status: "idle"
        chapterId: string
        storyId: string
        chapterTitle: string
        chapterStatus: "draft" | "published"
        chapterNumber: number
        onClick: () => void
  }
| {
        status: "selected"
        chapterId: string
        storyId: string
        chapterTitle: string
        chapterNumber: number
        chapterStatus: "draft" | "published"
        onClick: () => void
  }


const getStyles = (chapterStatus: "draft" | "published") => {
    switch (chapterStatus) {
        case "draft": return styles['draft']
        case "published": return styles['published']
    }
}


export function ChapterSidebarItem(props: ChapterSidebarItemProps) {
    switch (props.status) {
        case "idle": {
            return (
                <div
                    className={styles['content']}
                    onClick={props.onClick}
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
                    className={`${styles['content']} ${styles['selected']}`}
                    onClick={props.onClick}
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