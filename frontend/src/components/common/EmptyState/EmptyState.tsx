import type { ReactNode } from "react";

type EmptyStateProps = {
    headline: string
    title: string
    description?: string 
    action?: ReactNode
}

export function EmptyState({ headline, title, description, action }: EmptyStateProps) {
    return (
        <div className="card">
            <span className="system-badge system-badge__nobg">
                {`[${headline}]`}
            </span>
            <h2>{title}</h2>
            {description && (<p>{description}</p>)}
            {action}
        </div>
    )
}