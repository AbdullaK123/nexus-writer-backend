import { WelcomeHeader } from "./WelcomeHeader";
import { KpisRow } from "./KpisRow";
import { JumpBackInRow } from "./JumpBackInRow";
import { LibraryGrid } from "./LibraryGrid/LibraryGrid";
import { EmptyState } from "../../components/common"
import { DashboardLoadingSkeleton } from "./DashboardLoadingSkeleton";
import { useDashboardPage } from "./useDashboardPage";
import { LibraryLoadingSkeleton } from "./LibraryLoadingSkeleton";


export function DashboardPage() {

    const {
        welcomeHeader,
        dashboard,
        stories
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
                <div>
                    Error state goes here...
                </div>  
            )}
            {dashboard.isEmpty && (
                <EmptyState
                    headline="Your vault is empty"
                    title="Create a story to get started"
                />
            )}
            {dashboard.kpisRow && (
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
                <div>
                    Story error state goes here
                </div>
            )}
            {stories.libraryGrid && (
                <LibraryGrid 
                    {...stories.libraryGrid}
                />
            )}
        </div>
    )
}