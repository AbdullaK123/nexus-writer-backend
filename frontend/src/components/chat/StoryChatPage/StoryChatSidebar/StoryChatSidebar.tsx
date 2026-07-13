import { Button, Nothing } from "../../../common";
import { StoryChatSidebarItem, type StoryChatSidebarItemProps } from "./StoryChatSidebarItem";
import { PanelLeftOpen, PanelLeftClose  } from "lucide-react"
import styles from "./StoryChatSidebar.module.css"

export type StoryChatSidebarProps = 
| { status: "idle" }
| { status: "loading" }
| { status: "error" }
| { status: "empty" }
| {
    status: "ready",
    open: boolean,
    onOpenChange: (e: boolean) => void,
    storyTitle: string
    onNewThread: () => void
    items: StoryChatSidebarItemProps[]
  }


export function StoryChatSidebar(props: StoryChatSidebarProps) {
    switch (props.status) {
        case "empty":
        case "idle":
        case "error": {
            return <Nothing />
        }
        case "loading": {
            return (
                <div>
                    loading...
                </div>
            )
        }
        case "ready": {
            return (
                <div>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <span>{props.storyTitle}</span>
                            <Button
                                variant="primary"
                                onClick={props.onNewThread}
                            >
                                + New Thread
                            </Button>
                        </div>
                        {props.open ? (
                            <PanelLeftClose 
                                width={48}
                                height={48}
                                onClick={() => props.onOpenChange(false)}
                            />
                        ): (
                            <PanelLeftOpen
                                width={48}
                                height={48}
                                onClick={() => props.onOpenChange(true)}
                            />
                        )}
                    </div>
                    <div className={styles['items-container']}>
                        <span className="system-badge system-badge__nobg">
                            [RECENT]
                        </span>
                        {props.items.map((item, idx) => (
                            <StoryChatSidebarItem 
                                key={idx}
                                {...item}
                            />
                        ))}
                    </div>
                </div>
            )
        }
    }
}
