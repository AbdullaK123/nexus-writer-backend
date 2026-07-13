import { None } from "oxide.ts";
import { Button, ModalWithTrigger, Nothing } from "../../../common";
import styles from "./StoryChatHeader.module.css"

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
                <div className={styles['content']}>
                    <div className={styles['info-container']}>
                        <div className={styles['flex-row']}>
                            <span className="system-badge system-badge__nobg">
                                [THREAD]
                            </span>
                            <p className={styles['all-caps']}>{props.storyTitle}</p>
                        </div>
                        <h3>
                            {props.threadTitle}
                        </h3>
                    </div>
                    <div className={styles['action-container']}>
                        <ModalWithTrigger
                            open={props.renameModalOpen}
                            onOpenChange={props.onRenameModalOpenChange}
                            title={None}
                            description={None}
                            closeTrigger={None}
                            content={
                                <div className="flex-col">
                                    <h2>Give it a new title</h2>
                                    <div className="flex-row">
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
                                <div className="flex-col">
                                    <h2>Are you sure? This action can not be undone.</h2>
                                    <div className="flex-row">
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