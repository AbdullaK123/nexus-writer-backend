import styles from "./FilterChip.module.css"


type FilterChipProps = {
    status: "all" | "ongoing" | "hiatus" | "complete"
    count: number
    selected: boolean
    onClick: () => void;
}

export function FilterChip({ 
    status, 
    count, 
    selected, 
    onClick
 }: FilterChipProps) {
    return (
        <span
            className={selected ? `${styles['filter-chip']} ${styles['filter-chip__selected']}` : styles['filter-chip']}
            role="button"
            onClick={onClick}
        >
            `{status} - {count}`
        </span>
    )
}