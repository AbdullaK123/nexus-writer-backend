import { Button, LoadingSkeleton } from "../../../common";
import styles from "./StoryHeader.module.css"
import { None, Option } from "oxide.ts"

export type StoryHeaderProps = {
    storyTitle: Option<string>
    storyTitleStatus: "idle" | "loading" | "empty" | "error" | "success"
    onNavigateToLibrary: () => void
    onClickSettings: () => void
    onAskNexus: () => void
    onNewChapter: () => void
}

export function StoryHeader({
    storyTitle,
    storyTitleStatus,
    onNavigateToLibrary,
    onClickSettings,
    onAskNexus,
    onNewChapter
}: StoryHeaderProps) {

    const getStoryTitleState = (
        status: "idle" | "loading" | "empty" | "error" | "success",
        title: Option<string>
    ) => {
        switch (status) {
            case "idle": 
                return (
                    <LoadingSkeleton className={None} />
                )
            case "loading":
                return (
                    <LoadingSkeleton className={None} />
                )
            case "empty":
                return (
                    <Button
                        variant="ghost"
                        onClick={onNavigateToLibrary}
                    >
                        {`← YOUR LIBRARY`}
                    </Button>
                )
            case "error":
                return (
                    <p className={styles['red-text']}>X Failed to fetch story title.</p>
                )
            case "success":
                return (
                    <Button
                        variant="ghost"
                        onClick={onNavigateToLibrary}
                    >
                    {`← YOUR LIBRARY / ${title.unwrap().toUpperCase()}`}
                    </Button>
                )
        }
    }


    return (
        <div
            className={styles['header-container']}
        >
            {getStoryTitleState(storyTitleStatus, storyTitle)}
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