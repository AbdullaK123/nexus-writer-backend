import type { CommentCategory, CommentPriority, ExtractedComment } from "../../../../../infrastructure/api/types";
import { Button } from "../../../../common";
import styles from "./ChapterCommentCard.module.css"



export type ChapterCommentCardProps = 
{
    comment: ExtractedComment,
    onDismiss: () => void
    onDigIntoThis: () => void
}

const getCategoryBadgeStyle = (category: CommentCategory) => {
    switch (category) {
        case "character":
            return `${styles['badge']} ${styles['b-character']}`
        case "continuity":
            return `${styles['badge']} ${styles['b-continuity']}`
        case "clarity":
            return `${styles['badge']} ${styles['b-clarity']}`
        case "plot":
            return `${styles['badge']} ${styles['b-plot']}`
        case "structure":
            return `${styles['badge']} ${styles['b-structure']}`
        case "pacing":
            return `${styles['badge']} ${styles['b-pacing']}`
        case "dialogue":
            return `${styles['badge']} ${styles['b-dialogue']}`
        case "worldbuilding":
            return `${styles['badge']} ${styles['b-worldbuilding']}`
        case "prose":
            return `${styles['badge']} ${styles['b-prose']}`
    }
}

const getPriorityBadgeStyles = (priority: CommentPriority) => {
    switch (priority) {
        case "important":
            return `${styles['priority']} ${styles['p-important']}`
        case "suggestion":
            return `${styles['priority']} ${styles['p-suggestion']}`
        case "note":
            return `${styles['priority']} ${styles['p-note']}`
        default:
            return styles['priority']
    }
}


export function ChapterCommentCard(props: ChapterCommentCardProps) {
    return (
        <div className={styles['ccard']}>
            <div className={styles['ccard-top']}>
                <h3>
                    {props.comment.title}
                </h3>
                <span className={getCategoryBadgeStyle(props.comment.category)}>
                    {props.comment.category}
                </span>
                <span className={`${styles['badge']} ${styles['b-scope']}`}>
                    {props.comment.scope}
                </span>
            </div>
            <div className={styles['ccard-content']}>
                <blockquote className={styles['ccard-quote']}>
                    <p>
                        {props.comment.quoted_text}
                    </p>
                </blockquote>
                <p className={styles['ccard-body']}>
                    {props.comment.body}
                </p>
                {(props.comment.evidence.length > 0) && (
                    <div className={styles['ccard-ev-content']}>
                        <h4>EVIDENCE</h4>
                        {props.comment.evidence.map((evidence) => (
                            <>
                                <blockquote className={styles['ev-quote']}>
                                    <p>{evidence.quoted_text}</p>
                                </blockquote>
                                <p className={styles['ev-relevance']}>
                                    {evidence.relevance}
                                </p>
                            </>
                        ))}
                    </div>
                )}
            </div>
            <div className={styles['ccard-actions']}>
                <span className={getPriorityBadgeStyles(props.comment.priority)}>
                    {props.comment.priority}
                </span>
                <Button 
                    variant="ghost"
                    onClick={props.onDismiss}
                >
                    Dismiss
                </Button>
                <Button
                    variant="secondary"
                    onClick={props.onDigIntoThis}
                >
                    Dig Into This →
                </Button>
            </div>
        </div>
    )
}