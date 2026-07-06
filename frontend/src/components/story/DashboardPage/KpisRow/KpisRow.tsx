import { None, Some } from "oxide.ts";
import { Button, Card, EmptyState, ErrorState } from "../../../common"
import styles from "./KpisRow.module.css"
import { KpisRowLoadingSkeleton } from "./KpisRowLoadingSkeleton";

export type KpisRowProps =
  | { status: 'loading' }
  | { status: 'error'; onRetry: () => void }
  | { status: 'empty' }
  | {
      status: 'ready'
      totalWords: number
      storyCount: number
      totalChapters: number
      chaptersPublished: number
      totalScenesTracked: number
      currentStreak: number
    }

export function KpisRow(props: KpisRowProps) {
  switch (props.status) {
    case 'loading':
      return <KpisRowLoadingSkeleton />
    case 'error':
      return (
        <ErrorState
          headline="Error"
          title="Failed to load your progress."
          description={None}
          action={Some(<Button variant="primary" onClick={props.onRetry}>Retry</Button>)}
        />
      )
    case 'empty':
      return (
        <div className={styles['row-container']}>
          <div className={styles['space-between']}>
            <span className="system-badge system-badge__nobg">[YOUR PROGRESS]</span>
            <p>—</p>
          </div>
          <div className={styles['kpis-container']}>
            <EmptyState headline="No Data" title="Nothing to show yet" description={Some("Start writing to see your progress here.")} action={None} />
          </div>
        </div>
      )
    case 'ready': {
      const { totalWords, storyCount, totalChapters, chaptersPublished, totalScenesTracked, currentStreak } = props;
      return (
        <div className={styles['row-container']}>
          <div className={styles['space-between']}>
            <span className="system-badge system-badge__nobg">[YOUR PROGRESS]</span>
            <p>{`${currentStreak} day streak`}</p>
          </div>
          <div className={styles['kpis-container']}>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("TOTAL WORDS")}
              footer={Some(<p className="stat__caption">{`across ${storyCount} stories`}</p>)}
            >
              <h2 className="stat__value">{totalWords}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("CHAPTERS")}
              footer={Some(<p className="stat__caption">{chaptersPublished} published</p>)}
            >
              <h2 className="stat__value">{totalChapters}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("SCENES TRACKED")}
              footer={Some(<p className="stat__caption">extracted</p>)}
            >
              <h2 className="stat__value">{totalScenesTracked}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("STREAK")}
              footer={Some(<p className="stat__caption">days writing</p>)}
            >
              <h2 className="stat__value">{currentStreak}</h2>
            </Card>
          </div>
        </div>
      )
    }
  }
}