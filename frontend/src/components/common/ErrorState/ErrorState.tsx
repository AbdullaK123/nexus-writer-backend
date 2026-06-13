import type { ReactNode } from "react";
import styles from "./ErrorState.module.css"

type EmptyStateProps = {
    headline: string
    title: string
    description?: string 
    action?: ReactNode
}

export function ErrorState({ headline, title, description, action }: EmptyStateProps) {
    return (
        <div className="card">
            <span className={styles['logo']}>!</span>
            <span className={`system-badge system-badge__nobg ${styles['red-text']}`}>
                {`[${headline}]`}
            </span>
            <h2>{title}</h2>
            {description && (<p>{description}</p>)}
            {action}
        </div>
    )
}