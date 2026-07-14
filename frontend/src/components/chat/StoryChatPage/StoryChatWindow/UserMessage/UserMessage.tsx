import { Some, None, Option, match } from "oxide.ts";
import type { UserResponse } from "../../../../../infrastructure/api/types";
import { AvatarBadge, Nothing } from "../../../../common";
import { format } from "date-fns"
import ReactMarkdown from "react-markdown"
import styles from "./UserMessage.module.css"


export type UserMessageProps = {
    user: Option<UserResponse>
    createdAt: Date
    message: string
}


export function UserMessage(props: UserMessageProps) {
    return match(
        props.user,
        {
            Some: (user) => {
                return (
                    <div className="flex-col properly-wrap-text width-full">
                        <div className="flex-row">
                            <AvatarBadge 
                                username={user.username}
                                profileImgUrl={user.profileImg ? Some(user.profileImg) : None}
                            />
                            <span className="color-cyan all-caps">
                                {user.username} 
                            </span>
                            <span>
                                {`  ·  ${format(props.createdAt, 'HH:mm')}`}
                            </span>
                        </div>
                        <div className={styles['centered']}>
                            <ReactMarkdown
                                components={{
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
            },
            None: () => <Nothing />
        }
    )
}