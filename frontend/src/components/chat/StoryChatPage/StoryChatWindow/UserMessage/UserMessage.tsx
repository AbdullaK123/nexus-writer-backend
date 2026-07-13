import { Some, None, Option, match } from "oxide.ts";
import type { UserResponse } from "../../../../../infrastructure/api/types";
import { AvatarBadge, Nothing } from "../../../../common";
import { format } from "date-fns"


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
                    <div className="flex-row">
                        <AvatarBadge 
                            username={user.username}
                            profileImgUrl={user.profileImg ? Some(user.profileImg) : None}
                        />
                        <div className="flex-col properly-wrap-text">
                            <div>
                                <span className="color-cyan all-caps">
                                    {user.username} 
                                </span>
                                · {format(props.createdAt, 'HH:mm')}
                            </div>
                            <p>
                                {props.message}
                            </p>
                        </div>
                    </div>
                )
            },
            None: () => <Nothing />
        }
    )
}