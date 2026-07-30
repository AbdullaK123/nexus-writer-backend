import { Button, Nothing } from "../../../../common";
import styles from "./ChatComposer.module.css"

export type ChatComposerProps = 
| { status: "idle"}
| { status: "loading" }
| { status: "error" }
| { status: "empty"}
| { 
    status: "ready"
    query: string
    threadCreationPending: boolean
    onQueryChange: (query: string) => void
    onEnterDown: (query: string) => void
    onSubmit: (query: string) => void
  }


export function ChatComposer(props: ChatComposerProps) {
    switch (props.status) {
        case "idle":
        case "empty":
        case "error":
        case "loading": {
            return <Nothing /> // We'll show a 'page' loading skeleton if anything is still loading
        }
        case "ready": {
            return (
                <div className={styles['chat-composer-container']}>
                    {/*We'll use the field-sizing property to make it auto resizing */}
                    <textarea 
                        value={props.query}
                        className={styles['composer-textarea']}
                        rows={1}
                        onChange={(e) => props.onQueryChange(e.target.value)}
                        onKeyDown={(e) => {
                            if (e.key === "Enter" && !e.shiftKey) {
                                e.preventDefault()
                                if (!props.query.trim()) return
                                console.log("submit source: enter")
                                props.onEnterDown(props.query)
                            }
                        }}
                        placeholder="Ask anything about your story..."
                    />
                    <div className={styles['composer-actions']}>
                        <Button
                            variant="primary"
                            disabled={props.threadCreationPending}
                            className={styles['submit-btn']}
                            onClick={() => {
                                console.log("submit source: button")
                                props.onSubmit(props.query)
                            }}
                        >   
                            {props.threadCreationPending ? "Creating new thread ···" : "Ask →"}
                        </Button>
                    </div>
                </div>
            )
        }
    }
}