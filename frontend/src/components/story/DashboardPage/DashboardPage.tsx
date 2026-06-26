import { WelcomeHeader } from "./WelcomeHeader";
import { KpisRow } from "./KpisRow";
import { JumpBackInRow } from "./JumpBackInRow";
import { LibraryGrid } from "./LibraryGrid/LibraryGrid";
import { useDashboardPage } from "./useDashboardPage";
import styles from "./DashboardPage.module.css"

export function DashboardPage() {
  const { welcomeHeader, kpisRow, jumpBackInRow, libraryGrid } = useDashboardPage()

  return (
    <div className={styles['page-container']}>
      <WelcomeHeader {...welcomeHeader} />
      <KpisRow {...kpisRow} />
      <JumpBackInRow {...jumpBackInRow} />
      <LibraryGrid {...libraryGrid} />
    </div>
  )
}