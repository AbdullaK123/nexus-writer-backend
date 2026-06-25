import { useState } from "react";
import { AvatarBadge, SectionTag } from "../../../common";
import styles from "./WelcomeHeader.module.css"
import { Option } from "oxide.ts"

export type WelcomeHeaderProps = {
    username: string
    profileImageUrl: Option<string>;
    onEnterDown: (query: string) => void;
}


export function WelcomeHeader({ username, profileImageUrl, onEnterDown }: WelcomeHeaderProps) {

    const [query, setQuery] = useState("")

    return (
        <div className={styles['header-container']}>
            <div className={styles['welcome-section-container']}>
                <SectionTag 
                    sectionName={`${username} - online`}
                />
                <h2>Welcome Back.</h2>
            </div>
            <div className={styles['search-section-container']}>
                <input 
                    type="text"
                    value={query}
                    className="field__input"
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && query.trim() !== "") 
                            onEnterDown(query)
                    }}
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