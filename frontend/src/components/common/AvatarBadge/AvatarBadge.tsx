import { Avatar } from "@ark-ui/react/avatar"
import styles from "./AvatarBadge.module.css"

type AvatarBadgeProps = {
    username: string 
    profileImgUrl?: string 
}

export function AvatarBadge({ username, profileImgUrl }: AvatarBadgeProps) {
    return (
        <Avatar.Root className={styles['root']}>
            <Avatar.Fallback className={styles['fallback']}>
                {username.slice(0, 2)}
            </Avatar.Fallback>
            {profileImgUrl && (<Avatar.Image src={profileImgUrl} alt="avatar"/>)}
        </Avatar.Root>
    )
}