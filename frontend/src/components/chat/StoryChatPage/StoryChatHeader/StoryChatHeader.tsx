import { None } from "oxide.ts";
import { Button, ModalWithTrigger, Nothing } from "../../../common";


export type StoryChatHeaderProps = 
| { status: "idle" }
| { status: "loading" }
| { status: "error" }
| { status: "empty" }
| { 
    status: "ready"
    storyTitle: string
    threadTitle: string
    newThreadTitle: string
    onNewThreadTitleChange: (query: string) => void
    renameModalOpen: boolean
    onRenameModalOpenChange: (e: boolean) => void
    deleteModalOpen: boolean
    onDeleteModalOpenChange: (e: boolean) => void
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
                        <ModalWithTrigger
                            open={props.renameModalOpen}
                            onOpenChange={props.onRenameModalOpenChange}
                            title={None}
                            description={None}
                            closeTrigger={None}
                            content={
                                <div>
                                    <h2>Give it a new title</h2>
                                    <div>
                                        <input 
                                            value={props.newThreadTitle}
                                            onChange={(e) => props.onNewThreadTitleChange(e.target.value)}
                                            onKeyDown={(e) => {
                                                e.preventDefault()
                                                if (e.key === "Enter") props.onRename()
                                            }}
                                        />
                                        <Button
                                            variant="primary"
                                            onClick={props.onRename}
                                        >
                                            Submit
                                        </Button>
                                    </div>
                                </div>
                            }
                        >
                            <Button
                                variant="ghost"
                            >
                                Rename
                            </Button>
                        </ModalWithTrigger>
                        <Button
                            variant="ghost"
                            onClick={props.onExport}
                        >
                            Export
                        </Button>
                        <ModalWithTrigger
                            open={props.deleteModalOpen}
                            onOpenChange={props.onDeleteModalOpenChange}
                            title={None}
                            description={None}
                            closeTrigger={None}
                            content={
                                <div>
                                    <h2>Are you sure? This action can not be undone.</h2>
                                    <div>
                                        <Button
                                            variant="secondary"
                                            onClick={() =>props.onDeleteModalOpenChange(false)}
                                        >
                                            Delete
                                        </Button>
                                        <Button
                                            variant="danger"
                                            onClick={props.onDelete}
                                        >
                                            Yes I'm sure
                                        </Button>
                                    </div>
                                </div>
                            }
                        >
                            <Button
                                variant="ghost"
                            >
                                Delete
                            </Button>
                        </ModalWithTrigger>
                    </div>
                </div>
            )
    }
}