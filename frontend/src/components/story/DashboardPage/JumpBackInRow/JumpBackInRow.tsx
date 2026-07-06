import { None, Some } from "oxide.ts";
import { Button, EmptyState, ErrorState } from "../../../common";
import { ChapterCard, type ChapterCardProps } from "./ChapterCard/ChapterCard";
import styles from "./JumpBackInRow.module.css"
import { JumpBackInRowLoadingSkeleton } from "./JumpBackInRowLoadingSkeleton";

export type JumpBackInRowProps =
  | { status: 'loading' }
  | { status: 'error'; onRetry: () => void }
  | { status: 'empty' }
  | { status: 'ready'; chapterCards: ChapterCardProps[] }

export function JumpBackInRow(props: JumpBackInRowProps) {
  switch (props.status) {
    case 'loading':
      return <JumpBackInRowLoadingSkeleton />
    case 'error':
      return (
        <ErrorState
          headline="Error"
          title="Failed to load recent chapters."
          description={None}
          action={Some(<Button variant="primary" onClick={props.onRetry}>Retry</Button>)}
        />
      )
    case 'empty':
      return (
        <div className={styles['main-content']}>
          <div className={styles['header']}>
            <span className="system-badge system-badge__nobg">[JUMP BACK IN]</span>
            <p>Last 3 chapters you touched</p>
          </div>
          <div className={styles['content']}>
            <EmptyState
              headline="No Chapters."
              title="No chapters yet."
              description={Some("You haven't started writing any chapters yet. Click on any of your stories to start writing Chapter 1.")}
              action={None}
            />
          </div>
        </div>
      )
    case 'ready':
      return (
        <div className={styles['main-content']}>
          <div className={styles['header']}>
            <span className="system-badge system-badge__nobg">[JUMP BACK IN]</span>
            <p>Last 3 chapters you touched</p>
          </div>
          <div className={styles['content']}>
            {props.chapterCards.map((card, idx) => (
              <ChapterCard key={idx} {...card} />
            ))}
          </div>
        </div>
      )
  }
}