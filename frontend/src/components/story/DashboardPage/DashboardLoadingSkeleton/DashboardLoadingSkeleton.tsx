import { CardLoadingSkeleton } from "../../CardLoadingSkeleton";
import styles from "./DashboardLoadingSkeleton.module.css"

export function DashboardLoadingSkeleton() {
    return (
        <div className={styles['stacked']}>
            <div className={styles['kpis-skeleton']}>
                <CardLoadingSkeleton />
                <CardLoadingSkeleton />
                <CardLoadingSkeleton />
                <CardLoadingSkeleton />
            </div>
            <div className={styles['chapters-skeleton']}>
                <CardLoadingSkeleton />
                <CardLoadingSkeleton />
                <CardLoadingSkeleton />
            </div>
            <div>
                
            </div>
        </div>
    )
}