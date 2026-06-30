import { Button, EmptyState, ErrorState } from "../../../common";
import { ChapterListFilterBar, type ChapterListFilterBarProps } from "./ChapterListFilterBar/ChapterListFilterBar";
import { ChapterListItem, type ChapterListItemProps } from "./ChapterListItem/ChapterListItem";
import styles from "./ChapterList.module.css"
import { None, Some } from "oxide.ts";

export type ChapterListProps =
  | { status: 'loading' }
  | { status: 'error'; headline: string; title: string; onRetry: () => void }
  | { status: 'empty'; filterBar: ChapterListFilterBarProps }
  | { status: 'ready'; filterBar: ChapterListFilterBarProps; items: ChapterListItemProps[], selected: 'all' | 'draft' | 'published' }

export function ChapterList(props: ChapterListProps) {
  switch (props.status) {
    case 'loading':
      return (
        <div className={styles['content']}>
          {/* Could add a list skeleton here if desired */}
        </div>
      )
    case 'error':
      return (
        <div className={styles['content']}>
          <ErrorState
            headline={props.headline}
            title={props.title}
            description={None}
            action={Some(
              <Button variant="primary" onClick={props.onRetry}>Retry</Button>
            )}
          />
        </div>
      )
    case 'empty':
      return (
        <div className={styles['content']}>
          <ChapterListFilterBar {...props.filterBar} />
          <EmptyState
            headline="No chapters yet"
            title="Start chapter 1?"
            description={None}
            action={Some(<Button variant="primary">Take me to the editor</Button>)}
          />
        </div>
      )
    case 'ready':
      return (
        <div className={styles['content']}>
          <ChapterListFilterBar {...props.filterBar} />
          <div className={styles['list-items']}>
            {props.items.filter((chapter) => {
              if (props.selected === "all") 
                return true
              else
                return chapter.chapterStatus === props.selected
            }).map((item, idx) => (
              <ChapterListItem key={idx} {...item} />
            ))}
          </div>
        </div>
      )
  }
}

