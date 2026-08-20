import type { StatusBadgeVariant } from "../../../common";
import { StatusBadge } from "../../../common";
import { Option } from "oxide.ts";
import styles from "./StoryOverview.module.css";
import { StoryOverviewLoadingSkeleton } from "./StoryOverviewLoadingSkeleton";

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
        <StoryOverviewLoadingSkeleton />
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