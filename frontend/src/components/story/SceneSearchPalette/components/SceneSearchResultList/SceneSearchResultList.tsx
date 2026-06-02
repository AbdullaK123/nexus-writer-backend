import { SceneSearchLoadingSkeleton } from "../SceneSearchLoadingSkeleton";
import { SceneSearchResultItem, type SceneSearchResultItemProps } from "../SceneSearchResultItem"
import styles from "./SceneSearchResultList.module.css"

type SceneSearchResultListProps = {
    isLoading: boolean
    onSelectResult: (result: SceneSearchResultItemProps) => void
    results: SceneSearchResultItemProps[]
}

export function SceneSearchResultList({ isLoading, onSelectResult, results }: SceneSearchResultListProps) {

    if (isLoading) {
        return <SceneSearchLoadingSkeleton />
    }


    return (
        <div className={styles['scene-list-container']}>
            <p>
                {`SCENES - ${results.length} RESULTS`}
            </p>
            {results.map((result, idx) => (
                <SceneSearchResultItem 
                    key={idx}
                    {...result} 
                    onSelect={() => onSelectResult(result)}
                />
            ))}
        </div>
    )
}