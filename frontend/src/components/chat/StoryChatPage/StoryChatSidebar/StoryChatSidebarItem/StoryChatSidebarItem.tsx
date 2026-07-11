import { formatDistanceToNow } from "date-fns"


export type StoryChatSidebarItemProps = {
    storyId: string
    threadId: string
    threadTitle: string
    updatedAt: Date
    previewText: string
    onSelected: (storyId: string, threadId: string) => void
}


export function StoryChatSidebarItem(props: StoryChatSidebarItemProps) {
    return (
        <div
            role="button"
            onClick={() => props.onSelected(props.storyId, props.threadId)}
        >
            <div>
                <h3>{props.threadTitle}</h3>
                <span>{formatDistanceToNow(props.updatedAt, { addSuffix: true })}</span>
            </div>
            <p>{props.previewText}</p>
        </div>
    )
}