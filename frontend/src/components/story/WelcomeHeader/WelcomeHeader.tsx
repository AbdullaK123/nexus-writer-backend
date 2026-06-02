import { AvatarBadge, SectionTag } from "../../common";
import styles from "./WelcomeHeader.module.css"


type WelcomeHeaderProps = {
    username: string
    profileImageUrl?: string;
    query: string;
    onQueryChange: (query: string) => void;
}


export function WelcomeHeader({ username, profileImageUrl, query, onQueryChange }: WelcomeHeaderProps) {
    return (
        <div className={styles['header-container']}>
            <div className={styles['welcome-section-container']}>
                <SectionTag 
                    sectionName={`{username} - online`}
                />
                <h2>Welcome Back.</h2>
            </div>
            <div className={styles['search-section-container']}>
                <input 
                    type="text"
                    value={query}
                    onChange={() => onQueryChange(query)}
                    placeholder="Search scenes, chapters..."
                />
                <AvatarBadge 
                    username={username}
                    profileImgUrl={profileImageUrl}
                />
            </div>
        </div>
    )
}