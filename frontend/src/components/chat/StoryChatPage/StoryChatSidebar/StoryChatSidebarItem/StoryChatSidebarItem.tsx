import { formatDistanceToNow } from "date-fns"


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
            role="button"
            onClick={props.onSelected}
        >
            <h3>{props.threadTitle}</h3>
            <span>{formatDistanceToNow(props.updatedAt, { addSuffix: true })}</span>
        </div>
    )
}