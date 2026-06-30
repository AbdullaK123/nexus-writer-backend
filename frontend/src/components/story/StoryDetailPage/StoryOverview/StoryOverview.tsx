import type { StatusBadgeVariant } from "../../../common";
import { Button, ErrorState, LoadingSkeleton, StatusBadge } from "../../../common";
import { None, Some, Option } from "oxide.ts";
import styles from "./StoryOverview.module.css";

export type StoryOverviewProps =
  | { 
      status: 'idle',
      badge: StatusBadgeVariant
      startedText: string
      titleText: string
      stats: { totalChapters: number; totalWords: number; totalScenes: number; streakDays: number }
    }
  | { status: 'loading' }
  | {
      status: 'error'
      headline: string
      title: string
      description: string
      onRetryStats: () => void
      onRetrySummary: () => void
    }
  | {
      status: 'empty'
      badge: StatusBadgeVariant
      startedText: string
      titleText: string
    }
  | {
      status: 'ready'
      badge: StatusBadgeVariant
      startedText: string
      titleText: string
      summaryText: Option<string>
      stats: { totalChapters: number; totalWords: number; totalScenes: number; streakDays: number }
    }

export function StoryOverview(props: StoryOverviewProps) {
  switch (props.status) {
    case 'idle':
      return (
          <div className={styles['overview-container']}>
          <div className={styles['details-container']}>
            <div className={styles['details-header']}>
              <StatusBadge variant={props.badge} />
              <p className={styles['all-caps']}>{props.startedText}</p>
            </div>
            <div className={styles['summary-container']}>
              <h2>{props.titleText}</h2>
            </div>
          </div>
          <div className={styles['stats-container']}>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Chapters</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalChapters}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Words</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalWords}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Scenes</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalScenes}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Streak</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.streakDays}</p>
            </div>
          </div>
        </div>
      )
    case 'loading':
      return (
        <div className={styles['stats-container']}>
          <LoadingSkeleton className={None} />
          <LoadingSkeleton className={None} />
          <LoadingSkeleton className={None} />
          <LoadingSkeleton className={None} />
        </div>
      )

    case 'error':
      return (
        <ErrorState
          headline={props.headline}
          title={props.title}
          description={Some(props.description)}
          action={Some(
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <Button variant="primary" onClick={props.onRetryStats}>Retry Stats</Button>
              <Button variant="secondary" onClick={props.onRetrySummary}>Retry Summary</Button>
            </div>
          )}
        />
      )

    case 'empty':
      return (
        <div className={styles['overview-container']}>
          <div className={styles['details-container']}>
            <div className={styles['details-header']}>
              <StatusBadge variant={props.badge} />
              <p className={styles['all-caps']}>{props.startedText}</p>
            </div>
            <div className={styles['summary-container']}>
              <h2>{props.titleText}</h2>
              <p>No summary yet</p>
            </div>
          </div>
          <div className={styles['stats-container']}>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Chapters</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Words</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Scenes</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Streak</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>0</p>
            </div>
          </div>
        </div>
      )

    case 'ready':
      return (
        <div className={styles['overview-container']}>
          <div className={styles['details-container']}>
            <div className={styles['details-header']}>
              <StatusBadge variant={props.badge} />
              <p className={styles['all-caps']}>{props.startedText}</p>
            </div>
            <div className={styles['summary-container']}>
              <h2>{props.titleText}</h2>
              <p className={styles['summary']}>{props.summaryText.isSome() ? props.summaryText.unwrap() : ""}</p>
            </div>
          </div>
          <div className={styles['stats-container']}>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Chapters</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalChapters}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Words</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalWords}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Scenes</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.totalScenes}</p>
            </div>
            <div className={styles['stat']}>
              <p className={styles['all-caps']}>Streak</p>
              <p className={`${styles['all-caps']} ${styles['color-cyan']}`}>{props.stats.streakDays}</p>
            </div>
          </div>
        </div>
      )
  }
}