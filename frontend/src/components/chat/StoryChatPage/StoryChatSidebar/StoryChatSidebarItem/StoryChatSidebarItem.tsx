import { formatDistanceToNow } from "date-fns"
import styles from "./StoryChatSidebarItem.module.css"

export type StoryChatSidebarItemProps = {
    storyId: string
    threadId: string
    threadTitle: string
    active: boolean
    updatedAt: Date
    onSelected: () => void
}


export function StoryChatSidebarItem(props: StoryChatSidebarItemProps) {
    return (
        <div
            className={`${styles['sidebar-item']} ${props.active ? styles['active'] : ""}`}
            role="button"
            onClick={props.onSelected}
        >
            <h4>{props.threadTitle}</h4>
            <span>{formatDistanceToNow(props.updatedAt, { addSuffix: true })}</span>
        </div>
    )
}