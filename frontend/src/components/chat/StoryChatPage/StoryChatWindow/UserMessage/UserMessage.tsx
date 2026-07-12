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
                    <div>
                        <AvatarBadge 
                            username={user.username}
                            profileImgUrl={user.profileImg ? Some(user.profileImg) : None}
                        />
                        <div>
                            <span>
                                {user.username} · {format(props.createdAt, 'HH:mm')}
                            </span>
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