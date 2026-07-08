import { Tiptap, type Editor } from "@tiptap/react";
import { ChapterEditorContentLoadingSkeleton } from "./ChapterEditorContentLoadingSkeleton";
import { Button, ErrorState, Nothing } from "../../../../common";
import { Some, Option } from "oxide.ts";
import styles from "./ChapterEditorContent.module.css"

export type ChapterEditorContentProps = 
| { status: "empty", }
| { status: "loading" }
| { status: "error", onRetryChapter: () => void, onRetryStory: () => void }
| { status: "ready", editor: Option<Editor> }

export function ChapterEditorContent(props: ChapterEditorContentProps) {
    switch (props.status) {
        case "empty":
            return <Nothing />
        case "loading": {
            return <ChapterEditorContentLoadingSkeleton />
        }
        case "error": {
            return (
                <ErrorState 
                    headline="Error"
                    title="Failed to load your story data"
                    description={Some("Something went wrong. The server might be experiencing issues.")}
                    action={
                        Some(
                            <div className={styles['error-actions']}>
                                <Button
                                    variant="primary"
                                    onClick={props.onRetryChapter}
                                >
                                    Retry fetching chapter
                                </Button>
                                <Button
                                    variant="primary"
                                    onClick={props.onRetryStory}
                                >
                                    Retry fetching story
                                </Button>
                            </div>
                        )
                    }
                />
            )
        }
        case "ready": {
            if (props.editor.isNone()) return
            return (
                <div className={styles['editor-shell']}>
                    <Tiptap.Content/>
                </div>
            )
        }
    }


}

