import { LoadingSkeleton } from "../../common";
import styles from "./CardLoadingSkeleton.module.css"
import { Some } from "oxide.ts"

export function CardLoadingSkeleton() {
    return (
        <div className="card">
            <LoadingSkeleton className={Some(styles['width-50'])}/>
            <LoadingSkeleton className={Some(styles['width-80'])} />
            <LoadingSkeleton className={Some(styles['width-50'])}/>
        </div>
    )
}