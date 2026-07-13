import { None } from "oxide.ts";
import { AvatarBadge } from "../../../../common";
import ReactMarkdown  from "react-markdown"
import styles from "./AssistantMessage.module.css"


export type AssistantMessageProps = 
| { status: "streaming", message: string }
| {
    status: "done"
    message: string
  }


export function AssistantMessage(props: AssistantMessageProps) {
    switch (props.status) {
        case "streaming": {
            return (
                <div className="flex-col properly-wrap-text width-full">
                    <div className="flex-row">
                        <AvatarBadge 
                            username="Nexus"
                            profileImgUrl={None}
                        />
                        <span className="color-cyan">
                            NEXUS
                        </span>
                    </div>
                    <div className={styles['centered']}>
                         <ReactMarkdown>
                            {props.message}
                        </ReactMarkdown>
                    </div>
                </div>
            )
        }
        case "done": {
            return (
                <div className="flex-col properly-wrap-text width-full">
                    <div className="flex-row">
                        <AvatarBadge 
                            username="Nexus"
                            profileImgUrl={None}
                        />
                        <span className="color-cyan">
                            NEXUS
                        </span>
                    </div>
                     <div className={styles['centered']}>
                         <ReactMarkdown>
                            {props.message}
                        </ReactMarkdown>
                    </div>
                </div>
            )
        }
    }
}