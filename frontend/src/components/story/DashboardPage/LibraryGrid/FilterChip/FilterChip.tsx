import styles from "./FilterChip.module.css"


export type FilterChipProps =
  | { status: 'idle'; label: 'all' | 'ongoing' | 'hiatus' | 'complete' | 'draft' | 'published'; count: number; onClick: () => void }
  | { status: 'selected'; label: 'all' | 'ongoing' | 'hiatus' | 'complete' | 'draft' | 'published'; count: number; onClick: () => void }

export type FilterChipNoCountsProps =
  | { status: 'idle'; label: string; onClick: () => void }
  | { status: 'selected'; label: string; onClick: () => void }


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

export function FilterChipNoCounts(props: FilterChipNoCountsProps) {
  switch (props.status) {
    case 'idle':
      return (
        <span
          className={styles['filter-chip']}
          role="button"
          onClick={props.onClick}
        >
          {props.label}
        </span>
      )
    case 'selected':
      return (
        <span
          className={`${styles['filter-chip']} ${styles['filter-chip__selected']}`}
          role="button"
          onClick={props.onClick}
        >
          {props.label}
        </span>
      )
  }
}