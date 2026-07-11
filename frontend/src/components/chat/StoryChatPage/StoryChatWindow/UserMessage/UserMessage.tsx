import { Some, None } from "oxide.ts";
import type { UserResponse } from "../../../../../infrastructure/api/types";
import { AvatarBadge } from "../../../../common";
import { format } from "date-fns"


export type UserMessageProps = {
    user: UserResponse
    createdAt: Date
    message: string
}


export function UserMessage(props: UserMessageProps) {
    return (
        <div>
            <AvatarBadge 
                username={props.user.username}
                profileImgUrl={props.user.profileImg ? Some(props.user.profileImg) : None}
            />
            <div>
                <span>
                    {props.user.username} · {format(props.createdAt, 'HH:mm')}
                </span>
                <p>
                    {props.message}
                </p>
            </div>
        </div>
    )
}