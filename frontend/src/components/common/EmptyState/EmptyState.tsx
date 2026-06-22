import type { ReactNode } from "react";
import styles from "./EmptyState.module.css"

type EmptyStateProps = {
    headline: string
    title: string
    description?: string 
    action?: ReactNode
}

export function EmptyState({ headline, title, description, action }: EmptyStateProps) {
    return (
        <div className={`card ${styles['max-width']}`}>
            <span className={styles['logo']}>NX</span>
            <span className="system-badge system-badge__nobg">
                {`[${headline}]`}
            </span>
            <h2>{title}</h2>
            {description && (<p>{description}</p>)}
            {action}
        </div>
    )
}