import { WelcomeHeader } from "./WelcomeHeader";
import { KpisRow } from "./KpisRow";
import { JumpBackInRow } from "./JumpBackInRow";
import { LibraryGrid } from "./LibraryGrid/LibraryGrid";
import { Button, EmptyState, ErrorState } from "../../components/common"
import { DashboardLoadingSkeleton } from "./DashboardLoadingSkeleton";
import { useDashboardPage } from "./useDashboardPage";
import { LibraryLoadingSkeleton } from "./LibraryLoadingSkeleton";


export function DashboardPage() {

    const {
        welcomeHeader,
        dashboard,
        stories,
        refetch
    } = useDashboardPage()

    return (
        <div>
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
                        <Button
                            variant="primary"
                        >
                            Begin a new story →
                        </Button>
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