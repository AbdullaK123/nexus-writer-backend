import { Button,  Modal } from "../../../../common";
import styles from "./BeginNewStoryCard.module.css"
import { None } from "oxide.ts";

type BeginNewStoryCardProps = {
    storyTitle: string,
    onStoryTitleChange: (title: string) => void
    modalOpen: boolean
    onModalOpenChange: (e: boolean) => void
    onNewStory: (title: string) => void
}


export function BeginNewStoryCard({ 
    storyTitle,
    onStoryTitleChange,
    modalOpen, 
    onModalOpenChange, 
    onNewStory
 }: BeginNewStoryCardProps ) {
    return (
        <div className={styles['new-card-container']}>
            <Modal
                open={modalOpen}
                closeTrigger={None}
                title={None}
                description={None}
                onOpenChange={onModalOpenChange}
                content={
                    <div className={styles['form-container']}>
                        <h2>Create a new Story</h2>
                        <div className="hstack">
                            <input 
                                type="text"
                                value={storyTitle}
                                className="field__input"
                                placeholder="Give it a nice title..."
                                onChange={(e) => onStoryTitleChange(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") 
                                        onNewStory(storyTitle)
                                }}
                            />
                            <Button
                                variant="primary"
                                onClick={() => onNewStory(storyTitle)}
                            >
                                Submit
                            </Button>
                        </div>
                    </div>
                }
            >
                <span
                    className={styles['new-btn']}
                    role="button"
                >
                    +
                </span>
            </Modal>
            <h2>Begin a new story</h2>
            <p>Click to expand in place</p>
        </div>
    )
}