import { Tiptap, type Editor } from "@tiptap/react";
import { ChapterEditorContentLoadingSkeleton } from "./ChapterEditorContentLoadingSkeleton";
import { Nothing } from "../../../../common";
import { Option } from "oxide.ts";
import styles from "./ChapterEditorContent.module.css"

export type ChapterEditorContentProps = 
| { status: "empty", }
| { status: "loading" }
| { status: "ready", editor: Option<Editor> }

export function ChapterEditorContent(props: ChapterEditorContentProps) {
    switch (props.status) {
        case "empty":
            return <Nothing />
        case "loading": {
            return <ChapterEditorContentLoadingSkeleton />
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

