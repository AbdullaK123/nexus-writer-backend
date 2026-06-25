import type { ReactNode } from "react";
import styles from "./EmptyState.module.css"
import { match, Option } from "oxide.ts"

type EmptyStateProps = {
    headline: string
    title: string
    description: Option<string>
    action: Option<ReactNode>
}

export function EmptyState({ headline, title, description, action }: EmptyStateProps) {
    return (
        <div className={`card ${styles['max-width']}`}>
            <span className={styles['logo']}>NX</span>
            <span className="system-badge system-badge__nobg">
                {`[${headline}]`}
            </span>
            <h2>{title}</h2>
            {description.isSome() && (<p>{description.unwrap()}</p>)}
            {match(action, {
                Some: (action) => action,
                None: () => {}
            })}
        </div>
    )
}