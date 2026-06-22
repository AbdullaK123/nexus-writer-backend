import { CardLoadingSkeleton } from "../CardLoadingSkeleton"
import styles from "./LibraryLoadingSkeleton.module.css"

export function LibraryLoadingSkeleton() {
    return (
        <div className={styles['stories-loading']}>
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
        </div>
    )
}