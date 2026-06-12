import styles from "./BeginNewStoryCard.module.css"

type BeginNewStoryCardProps = {
    onClick: () => void
}


export function BeginNewStoryCard({ onClick }: BeginNewStoryCardProps ) {
    return (
        <div className={styles['new-card-container']}>
            <span
                className={styles['new-btn']}
                role="button"
                onClick={onClick}
            >
                +
            </span>
            <h2>Begin a new story</h2>
            <p>Click to expand in place</p>
        </div>
    )
}