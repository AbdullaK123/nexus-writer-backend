import { None } from "oxide.ts";
import { AvatarBadge } from "../../../../common";
import ReactMarkdown  from "react-markdown"
import styles from "./AssistantMessage.module.css"
import { ThreeDotsMoveIcon } from "./ThreeDotsMoveIcon";
import remarkGfm from "remark-gfm"




export type AssistantMessageProps = 
| { status: "loading" }
| { status: "streaming", message: string }
| {
    status: "done"
    message: string
  }


export function AssistantMessage(props: AssistantMessageProps) {
    switch (props.status) {
        case "loading": {
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
                         <ThreeDotsMoveIcon 
                            size={24}
                            color={"#00d4ff"}
                         />
                    </div>
                </div>
            )
        }
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
                         <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                table: ({ children }) => (
                                <div className={styles["md-table-scroll"]}>
                                    <table className={styles["md-table"]}>{children}</table>
                                </div>
                                ),
                                p: ({children}) => <p className={styles['md-paragraph']}>{children}</p>,
                                h2: ({children}) => <h2 className={styles['md-h-large']}>{children}</h2>,
                                h3: ({children}) => <h3 className={styles['md-h-large']}>{children}</h3>,
                                ol: ({children}) => <ol className={styles['md-list']}>{children}</ol>,
                                li: ({children}) => <li className={styles['md-list-item']}>{children}</li>
                            }}
                         >
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
                         <ReactMarkdown
                            remarkPlugins={[remarkGfm]}
                            components={{
                                table: ({ children }) => (
                                <div className={styles["md-table-scroll"]}>
                                    <table className={styles["md-table"]}>{children}</table>
                                </div>
                                ),
                                p: ({children}) => <p className={styles['md-paragraph']}>{children}</p>,
                                h2: ({children}) => <h2 className={styles['md-h-large']}>{children}</h2>,
                                h3: ({children}) => <h3 className={styles['md-h-large']}>{children}</h3>,
                                ol: ({children}) => <ol className={styles['md-list']}>{children}</ol>,
                                li: ({children}) => <li className={styles['md-list-item']}>{children}</li>
                            }}
                         >
                            {props.message}
                        </ReactMarkdown>
                    </div>
                </div>
            )
        }
    }
}