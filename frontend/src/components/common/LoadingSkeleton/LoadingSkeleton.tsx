import styles from "./LoadingSkeleton.module.css"
import { Option } from "oxide.ts"

type LoadingSkeletonProps = {
    className: Option<string >
}

export function LoadingSkeleton({ className }: LoadingSkeletonProps) {
    return (
        <div className={`${styles['skeleton']} ${className.isSome() ? className.unwrap() : "" }`} />
    )
}