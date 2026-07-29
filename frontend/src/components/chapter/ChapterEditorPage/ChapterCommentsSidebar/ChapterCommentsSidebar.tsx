import { Nothing } from "../../../common";
import { ChapterCommentCard, type ChapterCommentCardProps } from "./ChapterCommentCard";
import { ChapterCommentsSidebarHeader, type ChapterCommentsSidebarHeaderProps } from "./ChapterCommentsSidebarHeader";
import styles from "./ChapterCommentsSidebar.module.css"

export type ChapterCommentsSidebarProps = 
| { status: "loading"}
| { status: "empty" }
| { status: "idle" }
| { status: "error", onRetry: () => void}
| {
    status: "ready"
    header: ChapterCommentsSidebarHeaderProps,
    comments: ChapterCommentCardProps[]
  }

export function ChapterCommentsSidebar(props: ChapterCommentsSidebarProps) {
    switch (props.status) {
        case "idle": {
            return <Nothing />
        }
        case "loading": { // TODO: this needs a proper loading skeleton
            return (
                <div>
                    Loading... 
                </div>
            )
        }
        case "empty": { // TODO: this needs to be a proper empty state
            return (
                <div>
                    No comments yet.
                </div>
            )
        }
        case "error": { // TODO: proper error state needed here.
            return (
                <div>
                    Error
                </div>
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
                                if (props.header.activeCategory === "all") {
                                    return true
                                } else {
                                    return comment.comment.category === props.header.activeCategory
                                }
                            })
                            .map((comment) => (
                                <ChapterCommentCard 
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