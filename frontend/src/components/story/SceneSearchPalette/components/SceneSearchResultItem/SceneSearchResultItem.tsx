import styles from "./SceneSearchResultItem.module.css"

export type SceneSearchResultItemProps = {
    sceneTitle: string 
    chapterNumber: number 
    chapterTitle: string 
    sceneTension: "high" | "medium" | "low"
    scenePacing: "fast" | "steady" | "slow"
    sceneScore: number 
    onSelect: () => void
}

const getTensionStyles = (sceneTension: "high" | "medium" | "low") => {
    switch (sceneTension) {
        case "high":
            return `${styles['chip']} ${styles['chip__high']}`
        case "medium":
            return `${styles['chip']} ${styles['chip__medium']}`
        case "low":
            return `${styles['chip']} ${styles['chip__low']}`
    }
}

function TensionChip({ sceneTension }: { sceneTension: "high" | "medium" | "low" }) {
    return (
        <span className={getTensionStyles(sceneTension)}> 
            {sceneTension}
        </span>
    )
}

function PacingChip({ scenePacing }: { scenePacing: "fast" | "steady" | "slow" }) {
    return (
        <span className={`${styles['chip']} ${styles['chip__pacing']}`}> 
            {scenePacing}
        </span>
    )
}


export function SceneSearchResultItem({
    sceneTitle,
    chapterNumber,
    chapterTitle,
    sceneTension,
    scenePacing,
    sceneScore,
    onSelect
}: SceneSearchResultItemProps) {
    return (
        <div 
            role="button"
            tabIndex={0}
            className={styles['item-container']}
            onClick={onSelect}
        >
            <div className={styles['content-container']}>
                <h4>{sceneTitle}</h4>
                <div className={styles['row']}>
                    <p className={styles['muted-text']}>
                        {`CH ${chapterNumber} - ${chapterTitle}`}
                    </p>
                    <div className={styles['space-evenly']}>
                        <TensionChip sceneTension={sceneTension} />
                        <PacingChip scenePacing={scenePacing} />
                        <p className={styles['cyan-text']}>↵</p>
                    </div>
                </div>
            </div>
            <div className={styles['cyan-text']}>
                {sceneScore.toFixed(2)}
            </div>
        </div>
    )
}