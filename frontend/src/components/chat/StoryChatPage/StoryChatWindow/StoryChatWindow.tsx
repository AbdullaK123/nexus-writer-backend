import { Button, Nothing } from "../../../common";
import { AssistantMessage, type AssistantMessageProps } from "./AssistantMessage/AssistantMessage";
import { ChatComposer, type ChatComposerProps } from "./ChatComposer/ChatComposer";
import { UserMessage, type UserMessageProps } from "./UserMessage/UserMessage";


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
    messages: ConversationMessage[]
    composer: ChatComposerProps
  }


export function StoryChatWindow(props: StoryChatWindowProps) {
    switch (props.status) {
        case "idle": {
                return <Nothing />
        }
        case "loading": {
            return (
                <div>
                    Loading skeleton...
                </div>
            )
        }
        case "empty": {
            return (
                <div>
                    <h2>Let's talk about your book</h2>
                    <ChatComposer {...props.composer} />
                </div>
            )
        }
        case "error": {
            return (
                <div>
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
                <div>
                    <div>
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