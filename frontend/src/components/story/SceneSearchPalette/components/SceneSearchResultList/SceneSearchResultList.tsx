import { None, Some } from "oxide.ts";
import { Button, EmptyState, ErrorState } from "../../../../common";
import { SceneSearchLoadingSkeleton } from "../SceneSearchLoadingSkeleton";
import { SceneSearchResultItem } from "../SceneSearchResultItem"
import styles from "./SceneSearchResultList.module.css"
import type { SceneSearchResponse } from "../../../../../infrastructure/api/types";
import { useState } from "react";
import { useShortcut } from "../../../../../hooks/useShortcut";

export type SceneSearchResultListProps = 
| { status: "loading" }
| { status: "error", onRetry: () => void}
| { status: "empty" }
| {
    status: "ready"
    results: SceneSearchResponse[]
    onSelectResult: (chapterId: string) => void
  }

export function SceneSearchResultList(props: SceneSearchResultListProps) {

    const [selectedIdx, setSelectedIdx] = useState(0)

    useShortcut(
        "ArrowUp",
        false,
        false,
        () => {
            if (props.status === "ready" && selectedIdx > 0 ) {
                setSelectedIdx(prev => prev - 1)
            }
        }
    )

    useShortcut(
        "ArrowDown",
        false,
        false,
        () => {
             if (props.status === "ready" && selectedIdx < props.results.length - 1) {
                setSelectedIdx(prev => prev + 1)
            }
        }
    )

    useShortcut(
        "Enter",
        false,
        false,
        () => {
            if (props.status === "ready") {
                const selectedSceneChapter = props.results[selectedIdx].chapterId
                props.onSelectResult(selectedSceneChapter)
            }
        }
    )


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
                            selected={idx === selectedIdx}
                            key={idx}
                            sceneTitle={result.title}
                            scenePacing={result.pacing}
                            sceneScore={result.score}
                            sceneTension={result.tension}
                            chapterNumber={result.chapterNumber}
                            chapterTitle={result.chapterTitle}
                            onSelect={() => props.onSelectResult(result.chapterId)}
                        />
                    ))}
                </div>
            )
        }
    }
}