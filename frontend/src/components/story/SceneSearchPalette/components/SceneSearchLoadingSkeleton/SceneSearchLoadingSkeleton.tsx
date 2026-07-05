import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../../common"
import styles from "./SceneSearchLoadingSkeleton.module.css"

export function SceneSearchLoadingSkeleton() {
    return (
       <div className={styles.list}>
            {Array.from({ length: 4 }).map((_, index) => (
                <div key={index} className={styles.row}>
                    <div className={styles.main}>
                        <LoadingSkeleton className={Some(styles.title)} />
                        <div className={styles.metaRow}>
                            <LoadingSkeleton className={Some(styles.meta)} />
                            <LoadingSkeleton className={Some(styles.chip)} />
                            <LoadingSkeleton className={Some(styles.chip)} />
                        </div>
                    </div>
                    <LoadingSkeleton className={Some(styles.score)} />
                </div>
            ))}
        </div>
    )
}