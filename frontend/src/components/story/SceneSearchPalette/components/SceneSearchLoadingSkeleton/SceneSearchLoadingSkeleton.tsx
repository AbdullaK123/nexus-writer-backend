import { LoadingSkeleton } from "../../../../common"
import styles from "./SceneSearchLoadingSkeleton.module.css"

export function SceneSearchLoadingSkeleton() {
    return (
       <div className={styles.list}>
            {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className={styles.row}>
                    <div className={styles.main}>
                        <LoadingSkeleton className={styles.title} />
                        <div className={styles.metaRow}>
                            <LoadingSkeleton className={styles.meta} />
                            <LoadingSkeleton className={styles.chip} />
                            <LoadingSkeleton className={styles.chip} />
                        </div>
                    </div>
                    <LoadingSkeleton className={styles.score} />
                </div>
            ))}
        </div>
    )
}