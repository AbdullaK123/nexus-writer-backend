import { WelcomeHeader } from "./WelcomeHeader";
import { KpisRow } from "./KpisRow";
import { JumpBackInRow } from "./JumpBackInRow";
import { LibraryGrid } from "./LibraryGrid/LibraryGrid";
import { Button, EmptyState, ErrorState, Modal } from "../../common"
import { DashboardLoadingSkeleton } from "./DashboardLoadingSkeleton";
import { useDashboardPage } from "./useDashboardPage";
import { LibraryLoadingSkeleton } from "./LibraryLoadingSkeleton";
import styles from "./DashboardPage.module.css"
import { None, Some } from "oxide.ts";


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
                    description={Some("Sorry we couldn't load your dashboard. The server might be experiencing issues. Please try again.")}
                    action={
                        Some(<Button
                            variant="primary"
                            onClick={() => refetch.dashboard()}
                        >
                            Try Again
                        </Button>)
                    }
                />
            )}
            {stories.isEmpty && (
                <EmptyState
                    headline="No stories yet"
                    title="Your shelf is empty"
                    description={Some("Start with one story. Even a working title. The agent will read what you write as you write it, and the analytics fill in by themselves.")}
                    action={
                        Some(<Modal
                                open={stories.libraryGrid.modalOpen}
                                onOpenChange={stories.libraryGrid.onModalOpenChange}
                                closeTrigger={None}
                                title={None}
                                description={None}
                                content={
                                    <div className={styles['form-container']}>
                                        <h2>Create a new Story</h2>
                                        <div className="hstack">
                                            <input 
                                                type="text"
                                                value={stories.storyTitle}
                                                className="field__input"
                                                placeholder="Give it a nice title..."
                                                onChange={stories.onStoryTitleChange}
                                                onKeyDown={(e) => {
                                                    if (e.key === "Enter") 
                                                        stories.libraryGrid.onNewStory(stories.storyTitle)
                                                }}
                                            />
                                            <Button
                                                variant="primary"
                                                onClick={() => stories.libraryGrid.onNewStory(stories.storyTitle)}
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
                            </Modal>)
                    }
                />
            )}
            {!stories.isEmpty && dashboard.kpisRow && (
                <>
                    <KpisRow 
                        {...dashboard.kpisRow.unwrap()}
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
                    description={Some("Sorry we couldn't load your stories. The server might be experiencing issues. Please try again.")}
                    action={
                        Some(<Button
                            variant="primary"
                            onClick={() => refetch.stories()}
                        >
                            Try Again
                        </Button>)
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