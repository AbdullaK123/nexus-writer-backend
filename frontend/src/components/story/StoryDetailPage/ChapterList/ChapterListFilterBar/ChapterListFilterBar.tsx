import { FilterChip } from "../../../DashboardPage/LibraryGrid/FilterChip/FilterChip";
import styles from "./ChapterListFilterBar.module.css"

export type ChapterListFilterBarProps =
  | {
      status: 'ready'
      totalChapters: number
      totalDraftChapters: number
      totalPublishedChapters: number
      onClickFilterChip: (filter: 'all' | 'draft' | 'published') => void
      selected: 'all' | 'draft' | 'published'
    }

export function ChapterListFilterBar(props: ChapterListFilterBarProps) {
  switch (props.status) {
    case 'ready':
      return (
        <div className={styles['main-content']}>
          <div className={styles['count-container']}>
            <span className="system-badge system-badge__nobg">{`[CHAPTERS - ${props.totalChapters}]`}</span>
            <p>Most recent first</p>
          </div>
          <div className={styles['filter-chip-container']}>
            <FilterChip
              status="all"
              count={props.totalChapters}
              selected={props.selected === 'all'}
              onClick={() => props.onClickFilterChip('all')}
            />
            <FilterChip
              status="draft"
              count={props.totalDraftChapters}
              selected={props.selected === 'draft'}
              onClick={() => props.onClickFilterChip('draft')}
            />
            <FilterChip
              status="published"
              count={props.totalPublishedChapters}
              selected={props.selected === 'published'}
              onClick={() => props.onClickFilterChip('published')}
            />
          </div>
        </div>
      )
  }
}