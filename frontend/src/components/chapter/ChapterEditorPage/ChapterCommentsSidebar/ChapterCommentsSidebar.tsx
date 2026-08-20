import { LoadingSkeleton, Nothing } from "../../../common";
import { ChapterCommentCard, type ChapterCommentCardProps } from "./ChapterCommentCard";
import { ChapterCommentsSidebarHeader, type ChapterCommentsSidebarHeaderProps } from "./ChapterCommentsSidebarHeader";
import styles from "./ChapterCommentsSidebar.module.css"
import { Some } from "oxide.ts";

export type ChapterCommentsSidebarProps = 
| { status: "loading"}
| { status: "empty" }
| { status: "idle" }
| {
    status: "ready"
    header: ChapterCommentsSidebarHeaderProps,
    comments: ChapterCommentCardProps[]
  }

export function ChapterCommentsSidebar(props: ChapterCommentsSidebarProps) {
    switch (props.status) {
        case "empty":
        case "idle": {
            return <Nothing />
        }
        case "loading": { // TODO: this needs a proper loading skeleton
            return (
                <aside className={styles['content']}>
                    <LoadingSkeleton className={Some(`${styles['h-30']} ${styles['w-full']}`)} />
                    <div className={styles['items-container']}>
                        <LoadingSkeleton className={Some(`${styles['h-15']} ${styles['w-full']}`)} />
                        <LoadingSkeleton className={Some(`${styles['h-15']} ${styles['w-full']}`)} />
                        <LoadingSkeleton className={Some(`${styles['h-15']} ${styles['w-full']}`)} />
                        <LoadingSkeleton className={Some(`${styles['h-15']} ${styles['w-full']}`)} />
                    </div>
                </aside>
            )
        }
        case "ready": {
            return (
                <aside 
                    className={`${styles['content']} ${props.header.sidebarOpen ? "" : styles['closed']}`}
                >
                    <ChapterCommentsSidebarHeader 
                        {...props.header} 
                    />
                    <div className={styles['items-container']}>
                        {props
                            .comments
                            .filter((comment) => {
                                return props.header.view === comment.view
                            })
                            .filter((comment) => {
                                if (props.header.activeCategory === "all") {
                                    return true
                                } else {
                                    return comment.comment.category === props.header.activeCategory
                                }
                            })
                            .map((comment) => (
                                <ChapterCommentCard 
                                    key={comment.comment.issue_key}
                                    {...comment}
                                />
                            ))
                        }
                    </div>
                </aside>
            )
        }
    }
}