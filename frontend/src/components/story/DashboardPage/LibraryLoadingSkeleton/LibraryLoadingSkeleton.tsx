import { CardLoadingSkeleton } from "../../CardLoadingSkeleton"
import styles from "./LibraryLoadingSkeleton.module.css"

export function LibraryLoadingSkeleton() {
    return (
        <div className={styles['stories-skeleton']}>
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
            <CardLoadingSkeleton />
        </div>
    )
}