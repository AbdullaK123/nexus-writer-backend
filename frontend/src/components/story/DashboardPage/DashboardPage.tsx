import { WelcomeHeader } from "./WelcomeHeader";
import { KpisRow } from "./KpisRow";
import { JumpBackInRow } from "./JumpBackInRow";
import { LibraryGrid } from "./LibraryGrid/LibraryGrid";
import { Button, EmptyState, ErrorState, Modal } from "../../common"
import { DashboardLoadingSkeleton } from "./DashboardLoadingSkeleton";
import { useDashboardPage } from "./useDashboardPage";
import { LibraryLoadingSkeleton } from "./LibraryLoadingSkeleton";
import styles from "./DashboardPage.module.css"


export function DashboardPage() {

    const {
        welcomeHeader,
        dashboard,
        stories,
        refetch
    } = useDashboardPage()

    return (
        <div className={styles['page-container']}>
            <WelcomeHeader 
                {...welcomeHeader}
            />
            {dashboard.isLoading && (
                <DashboardLoadingSkeleton />
            )} 
            {dashboard.isError && (
                <ErrorState 
                    headline="Error"
                    title="Failed to load your dashboard."
                    description="Sorry we couldn't load your dashboard. The server might be experiencing issues. Please try again."
                    action={
                        <Button
                            variant="primary"
                            onClick={() => refetch.dashboard()}
                        >
                            Try Again
                        </Button>
                    }
                />
            )}
            {stories.isEmpty && (
                <EmptyState
                    headline="No stories yet"
                    title="Your shelf is empty"
                    description="Start with one story. Even a working title. The agent will read what you write as you write it, and the analytics fill in by themselves."
                    action={
                        <Modal
                            open={stories.libraryGrid.modalOpen}
                            onOpenChange={stories.libraryGrid.onModalOpenChange}
                            content={
                                <div className={styles['form-container']}>
                                    <h2>Create a new Story</h2>
                                    <div className="hstack">
                                        <input 
                                            type="text"
                                            value={stories.libraryGrid.storyTitle}
                                            className="field__input"
                                            placeholder="Give it a nice title..."
                                            onChange={stories.libraryGrid.onStoryTitleChange}
                                            onKeyDown={(e) => {
                                                if (e.key === "Enter") 
                                                    stories.libraryGrid.onNewStory(stories.libraryGrid.storyTitle)
                                            }}
                                        />
                                        <Button
                                            variant="primary"
                                            onClick={() => stories.libraryGrid.onNewStory(stories.libraryGrid.storyTitle)}
                                        >
                                            Submit
                                        </Button>
                                    </div>
                                </div>
                            }
                        >
                            <Button
                                variant="primary"
                            >
                                Begin a new story →
                            </Button>
                        </Modal>
                    }
                />
            )}
            {!stories.isEmpty && dashboard.kpisRow && (
                <>
                    <KpisRow 
                        {...dashboard.kpisRow}
                    />
                    <JumpBackInRow 
                        {...dashboard.jumpBackInRow}
                    />
                </>
            )}
            {stories.isLoading && (
                <LibraryLoadingSkeleton />
            )}
            {stories.isError && (
                <ErrorState 
                    headline="Error"
                    title="Failed to load your stories."
                    description="Sorry we couldn't load your stories. The server might be experiencing issues. Please try again."
                    action={
                        <Button
                            variant="primary"
                            onClick={() => refetch.stories()}
                        >
                            Try Again
                        </Button>
                    }
                />
            )}
            {!stories.isEmpty && (
                <LibraryGrid 
                    {...stories.libraryGrid}
                />
            )}
        </div>
    )
}