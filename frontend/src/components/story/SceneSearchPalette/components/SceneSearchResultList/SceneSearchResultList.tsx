import { None, Some } from "oxide.ts";
import { Button, EmptyState, ErrorState } from "../../../../common";
import { SceneSearchLoadingSkeleton } from "../SceneSearchLoadingSkeleton";
import { SceneSearchResultItem, type SceneSearchResultItemProps } from "../SceneSearchResultItem"
import styles from "./SceneSearchResultList.module.css"

export type SceneSearchResultListProps = 
| { status: "loading" }
| { status: "error", onRetry: () => void}
| { status: "empty" }
| {
    status: "ready"
    onSelectResult: (result: SceneSearchResultItemProps) => void
    results: SceneSearchResultItemProps[]
  }

export function SceneSearchResultList(props: SceneSearchResultListProps) {
    switch (props.status) {
        case "loading": {
            return <SceneSearchLoadingSkeleton />
        }
        case "error": {
            return (
                <ErrorState 
                    headline="Search error"
                    title="Failed to find scenes"
                    description={Some("Something went wrong. The server might be experiencing issues.")}
                    action={Some(
                        <Button 
                            variant="primary"
                            onClick={props.onRetry}
                        >
                            Retry
                        </Button>
                    )}
                />
            )
        }
        case "empty": {
            return (
                <EmptyState 
                    headline="No scenes found"
                    title="Your query returned no results. Try a different one"
                    description={None}
                    action={None}
                />
            )
        }
        case "ready": {
            return (
                <div className={styles['scene-list-container']}>
                    <h4>
                        {`SCENES - ${props.results.length} RESULTS`}
                    </h4>
                    {props.results.map((result, idx) => (
                        <SceneSearchResultItem 
                            key={idx}
                            {...result} 
                            onSelect={() => props.onSelectResult(result)}
                        />
                    ))}
                </div>
            )
        }
    }
}