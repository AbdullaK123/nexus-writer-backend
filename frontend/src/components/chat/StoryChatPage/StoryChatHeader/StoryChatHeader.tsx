import { Button, Nothing } from "../../../common";


export type StoryChatHeaderProps = 
| { status: "loading" }
| { status: "error" }
| { status: "empty" }
| { 
    status: "ready"
    storyTitle: string
    threadTitle: string
    onRename: () => void
    onExport: () => void
    onDelete: () => void
  }


export function StoryChatHeader(props: StoryChatHeaderProps) {
    switch (props.status) {
        case "empty":
        case "error":
            return <Nothing />
        case "loading":
            return (
                <div>
                    Loading...
                </div>
            )
        case "ready":
            return (
                <div>
                    <div>
                        <div>
                            <span>
                                [THREAD]
                            </span>
                            <p>{props.storyTitle}</p>
                        </div>
                        <h3>
                            {props.threadTitle}
                        </h3>
                    </div>
                    <div>
                        <Button
                            variant="ghost"
                            onClick={props.onRename}
                        >
                            Rename
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={props.onExport}
                        >
                            Export
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={props.onDelete}
                        >
                            Delete
                        </Button>
                    </div>
                </div>
            )
    }
}