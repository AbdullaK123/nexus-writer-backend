import { formatDistanceToNow } from "date-fns"
import styles from "./StoryChatSidebarItem.module.css"

export type StoryChatSidebarItemProps = {
    storyId: string
    threadId: string
    threadTitle: string
    updatedAt: Date
    onSelected: () => void
}


export function StoryChatSidebarItem(props: StoryChatSidebarItemProps) {
    return (
        <div
            className={styles['sidebar-item']}
            role="button"
            onClick={props.onSelected}
        >
            <h3>{props.threadTitle}</h3>
            <span>{formatDistanceToNow(props.updatedAt, { addSuffix: true })}</span>
        </div>
    )
}