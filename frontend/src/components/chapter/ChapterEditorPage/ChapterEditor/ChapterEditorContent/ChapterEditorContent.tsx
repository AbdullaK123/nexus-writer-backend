import { Tiptap, type Editor } from "@tiptap/react";
import { ChapterEditorContentLoadingSkeleton } from "./ChapterEditorContentLoadingSkeleton";
import { Button, ErrorState } from "../../../../common";
import { Some, Option } from "oxide.ts";
import styles from "./ChapterEditorContent.module.css"

export type ChapterEditorContentProps = 
| { status: "loading" }
| { status: "error", onRetry: () => void }
| { status: "ready", editor: Option<Editor>, content: string }

export function ChapterEditorContent(props: ChapterEditorContentProps) {
    switch (props.status) {
        case "loading": {
            return <ChapterEditorContentLoadingSkeleton />
        }
        case "error": {
            return (
                <ErrorState 
                    headline="Error"
                    title="Failed to load your chapter"
                    description={Some("Something went wrong. The server might be experiencing issues.")}
                    action={
                        Some(
                            <Button
                                variant="primary"
                                onClick={props.onRetry}
                            >
                                Retry
                            </Button>
                        )
                    }
                />
            )
        }
        case "ready": {
            if (props.editor.isNone()) return
            return (
                <div className={styles['editor-shell']}>
                    <Tiptap editor={props.editor.unwrap()}>
                        <Tiptap.Content/>
                    </Tiptap>
                </div>
            )
        }
    }


}

