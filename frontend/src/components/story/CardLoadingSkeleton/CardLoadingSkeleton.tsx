import { LoadingSkeleton } from "../../common";
import styles from "./CardLoadingSkeleton.module.css"

export function CardLoadingSkeleton() {
    return (
        <div className="card">
            <LoadingSkeleton className={styles['width-50']}/>
            <LoadingSkeleton className={styles['width-80']} />
            <LoadingSkeleton className={styles['width-50']}/>
        </div>
    )
}