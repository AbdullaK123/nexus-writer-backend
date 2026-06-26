import styles from "./FilterChip.module.css"


export type FilterChipProps =
  | { status: 'idle'; label: 'all' | 'ongoing' | 'hiatus' | 'complete' | 'draft' | 'published'; count: number; onClick: () => void }
  | { status: 'selected'; label: 'all' | 'ongoing' | 'hiatus' | 'complete' | 'draft' | 'published'; count: number; onClick: () => void }

export function FilterChip(props: FilterChipProps) {
  switch (props.status) {
    case 'idle':
      return (
        <span
          className={styles['filter-chip']}
          role="button"
          onClick={props.onClick}
        >
          {`${props.label} - ${props.count}`}
        </span>
      )
    case 'selected':
      return (
        <span
          className={`${styles['filter-chip']} ${styles['filter-chip__selected']}`}
          role="button"
          onClick={props.onClick}
        >
          {`${props.label} - ${props.count}`}
        </span>
      )
  }
}