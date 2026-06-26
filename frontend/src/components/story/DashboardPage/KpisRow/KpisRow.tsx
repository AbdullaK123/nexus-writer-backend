import { None, Some } from "oxide.ts";
import { Card } from "../../../common"
import styles from "./KpisRow.module.css"

import { Button, ErrorState } from "../../../common";

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
      return (
        <div className={styles['row-container']}>
          <div className={styles['space-between']}>
            <span className="system-badge system-badge__nobg">[YOUR PROGRESS]</span>
            <p>Loading…</p>
          </div>
          <div className={styles['kpis-container']}>
            {[1,2,3,4].map((i) => (
              <Card key={i} className="stat" cardTitle={None} subtitle={None} header={Some(" ")} footer={Some(<p className="stat__caption">&nbsp;</p>)}>
                <h2 className="stat__value">—</h2>
              </Card>
            ))}
          </div>
        </div>
      )
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
            <p>No activity yet</p>
          </div>
        </div>
      )
    case 'ready':
      return (
        <div className={styles['row-container']}>
          <div className={styles['space-between']}>
            <span className="system-badge system-badge__nobg">[YOUR PROGRESS]</span>
            <p>{`${props.currentStreak} day streak`}</p>
          </div>
          <div className={styles['kpis-container']}>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("TOTAL WORDS")}
              footer={Some(<p className="stat__caption">{`across ${props.storyCount} stories`}</p>)}
            >
              <h2 className="stat__value">{props.totalWords}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("CHAPTERS")}
              footer={Some(<p className="stat__caption">{props.chaptersPublished} published</p>)}
            >
              <h2 className="stat__value">{props.totalChapters}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("SCENES TRACKED")}
              footer={Some(<p className="stat__caption">extracted</p>)}
            >
              <h2 className="stat__value">{props.totalScenesTracked}</h2>
            </Card>
            <Card
              className="stat"
              cardTitle={None}
              subtitle={None}
              header={Some("STREAK")}
              footer={Some(<p className="stat__caption">days writing</p>)}
            >
              <h2 className="stat__value">{props.currentStreak}</h2>
            </Card>
          </div>
        </div>
      )
  }
}