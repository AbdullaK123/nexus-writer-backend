import { Button } from "../../../common";
import styles from "./StoryHeader.module.css"


export type StoryHeaderProps = {
    storyTitle: string
    onNavigateToLibrary: () => void
    onClickSettings: () => void
    onAskNexus: () => void
    onNewChapter: () => void
}

export function StoryHeader({
    storyTitle,
    onNavigateToLibrary,
    onClickSettings,
    onAskNexus,
    onNewChapter
}: StoryHeaderProps) {
    return (
        <div
            className={styles['header-container']}
        >
            <Button
                variant="ghost"
                onClick={onNavigateToLibrary}
            >
               {`← YOUR LIBRARY / ${storyTitle.toUpperCase()}`}
            </Button>
            <div
                className={styles['btn-container']}
            >
                <Button
                    variant="secondary"
                    onClick={onClickSettings}
                >
                    Settings
                </Button>
                <Button 
                    variant="primary"
                    onClick={onAskNexus}
                >
                    Ask Nexus
                </Button>
                <Button
                    variant="primary"
                    onClick={onNewChapter}
                >
                    + New Chapter
                </Button>
            </div>
        </div>
    )
}