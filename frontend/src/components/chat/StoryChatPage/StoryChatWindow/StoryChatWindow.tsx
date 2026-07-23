import { Button, LoadingSkeleton, Nothing } from "../../../common";
import { AssistantMessage, type AssistantMessageProps } from "./AssistantMessage/AssistantMessage";
import { ChatComposer, type ChatComposerProps } from "./ChatComposer/ChatComposer";
import { UserMessage, type UserMessageProps } from "./UserMessage/UserMessage";
import styles from "./StoryChatWindow.module.css"
import { None } from "oxide.ts";


export type ConversationMessage = 
| { type: "user", props: UserMessageProps }
| { type: "assistant", props: AssistantMessageProps }


export type StoryChatWindowProps = 
| { status: "idle" }
| { status: "loading" }
| { status: "empty", composer: ChatComposerProps }
| { status: "error", onRetry: () => void}
| { 
    status: "ready"
    onMessagesScroll: () => void
    messages: ConversationMessage[]
    composer: ChatComposerProps
  }


export function StoryChatWindow(props: StoryChatWindowProps) {
    switch (props.status) {
        case "idle":
        case "empty": {
            return <Nothing />
        }
        case "loading": {
            return (
                <div className={styles['content']}>
                    <div className={styles['messages-container']}>
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                        <LoadingSkeleton className={None} />
                    </div>
                </div>
            )
        }
        case "error": {
            return (
                <div className={styles['content']}>
                    <h2>Something went wrong.</h2>
                    <Button
                        variant="primary"
                        onClick={props.onRetry}
                    >
                        Retry
                    </Button>
                </div>
            )
        }
        case "ready": {
            return (
                <div className={styles['content']}>
                    <div 
                        id="messages-container" 
                        className={styles['messages-container']}
                        onScroll={props.onMessagesScroll}
                    >
                        {props.messages.map((msg, idx) => {
                            switch (msg.type) {
                                case "user": return <UserMessage key={idx} {...msg.props} />
                                case "assistant": return <AssistantMessage key={idx} {...msg.props} />
                            }
                        })}
                    </div>
                    <ChatComposer {...props.composer} />
                </div>
            )
        }
    }
}