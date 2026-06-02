import styles from "./LoadingSkeleton.module.css"

type LoadingSkeletonProps = {
    className?: string 
}

export function LoadingSkeleton({ className }: LoadingSkeletonProps) {
    return (
        <div className={`${styles['skeleton']} ${className ? className : undefined}`} />
    )
}