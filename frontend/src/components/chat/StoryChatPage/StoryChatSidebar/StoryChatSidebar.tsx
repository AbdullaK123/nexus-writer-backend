import { Button, Nothing } from "../../../common";
import { StoryChatSidebarItem, type StoryChatSidebarItemProps } from "./StoryChatSidebarItem";
import { PanelLeftOpen, PanelLeftClose  } from "lucide-react"


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
                    <div>
                        <div>
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
                    <aside>
                        <span>
                            [ RECENT ]
                        </span>
                        {props.items.map((item, idx) => (
                            <StoryChatSidebarItem 
                                key={idx}
                                {...item}
                            />
                        ))}
                    </aside>
                </div>
            )
        }
    }
}
