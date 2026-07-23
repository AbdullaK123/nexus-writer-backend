import { Button, LoadingSkeleton, Nothing } from "../../../common";
import { StoryChatSidebarItem, type StoryChatSidebarItemProps } from "./StoryChatSidebarItem";
import { PanelLeftOpen, PanelLeftClose  } from "lucide-react"
import styles from "./StoryChatSidebar.module.css"
import { None } from "oxide.ts";

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
                <div className={styles['content']}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <LoadingSkeleton className={None}/>
                            <LoadingSkeleton className={None}/>
                        </div>
                        <LoadingSkeleton className={None}/>
                    </div>
                    <div className={styles['items-container']}>
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                    </div>
                </div>
            )
        }
        case "ready": {
            return (
                <div className={`${styles['content']} ${props.open ? "" : styles['closed']}`}>
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
                        <span
                            className={styles['icon-btn']}
                            onClick={() => props.onOpenChange(!props.open)}
                        >
                            {props.open ? (
                                <PanelLeftClose
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            ): (
                                <PanelLeftOpen
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            )}
                        </span>
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
