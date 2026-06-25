import type { ReactNode } from "react";
import styles from "./ErrorState.module.css"
import { Option, match } from "oxide.ts"

type EmptyStateProps = {
    headline: string
    title: string
    description: Option<string>
    action: Option<ReactNode>
}

export function ErrorState({ headline, title, description, action }: EmptyStateProps) {
    return (
        <div className="card">
            <span className={styles['logo']}>!</span>
            <span className={`system-badge system-badge__nobg ${styles['red-text']}`}>
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