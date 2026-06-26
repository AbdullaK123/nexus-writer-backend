import { formatDistanceToNow } from "date-fns"
import styles from "./ChapterListItem.module.css"

export type ChapterListItemBase = {
  chapterNumber: number
  chapterTitle: string
  chapterStatus: "draft" | "published"
  updatedAt: Date
  wordCount: number
  onClick: () => void
  onDoubleClick: () => void
}

export type ChapterListItemProps =
  | (ChapterListItemBase & { status: 'idle' })
  | (ChapterListItemBase & { status: 'selected' })

export function ChapterListItem(props: ChapterListItemProps) {
  switch (props.status) {
    case 'idle':
      return (
        <div
          className={`${styles['content']}`}
          onClick={props.onClick}
          onDoubleClick={props.onDoubleClick}
        >
          <div className={styles['chapter-info-container']}>
            <p className={styles['chapter-number']}>{props.chapterNumber}</p>
            <div className={styles['chapter-info']}>
              <h4>{props.chapterTitle}</h4>
              <p className={props.chapterStatus === 'draft' ? `${styles['draft']} ${styles['all-caps']}` : styles['all-caps']}>
                {props.chapterStatus === 'draft'
                  ? 'DRAFT'
                  : `EDITED ${formatDistanceToNow(props.updatedAt, { addSuffix: true })}`}
              </p>
            </div>
          </div>
          <div className={styles['all-caps']}>
            <p>{`${props.wordCount} WORDS`}</p>
          </div>
        </div>
      )
    case 'selected':
      return (
        <div
          className={`${styles['content']} ${styles['selected']}`}
          onClick={props.onClick}
          onDoubleClick={props.onDoubleClick}
        >
          <div className={styles['chapter-info-container']}>
            <p className={styles['chapter-number']}>{props.chapterNumber}</p>
            <div className={styles['chapter-info']}>
              <h4>{props.chapterTitle}</h4>
              <p className={props.chapterStatus === 'draft' ? `${styles['draft']} ${styles['all-caps']}` : styles['all-caps']}>
                {props.chapterStatus === 'draft'
                  ? 'DRAFT'
                  : `EDITED ${formatDistanceToNow(props.updatedAt, { addSuffix: true })}`}
              </p>
            </div>
          </div>
          <div className={styles['all-caps']}>
            <p>{`${props.wordCount} WORDS`}</p>
          </div>
        </div>
      )
  }
}