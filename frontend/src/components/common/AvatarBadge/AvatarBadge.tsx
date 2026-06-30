import { Avatar } from "@ark-ui/react/avatar"
import styles from "./AvatarBadge.module.css"
import { Option } from "oxide.ts"

type AvatarBadgeProps = {
    username: string 
    profileImgUrl: Option<string> 
}

export function AvatarBadge({ username, profileImgUrl }: AvatarBadgeProps) {
    return (
        <Avatar.Root className={styles['root']}>
            <Avatar.Fallback className={styles['fallback']}>
                {username.slice(0,2)}
            </Avatar.Fallback>
            {profileImgUrl && (<Avatar.Image src={profileImgUrl.isSome() ? profileImgUrl.unwrap() : ""} alt="avatar"/>)}
        </Avatar.Root>
    )
}