import { ChapterEditor } from "./ChapterEditor/ChapterEditor";
import { ChapterEditorSidebar } from "./ChapterEditorSidebar";
import { useChapterEditorPage } from "./useChapterEditorPage";
import styles from "./ChapterEditorPage.module.css"
import { Tiptap } from "@tiptap/react";


export function ChapterEditorPage() {

    const { sidebar, editorProps, tipTapEditor } = useChapterEditorPage()

    return (
        <Tiptap editor={tipTapEditor}>
            <div className={styles['page-container']}>
                <ChapterEditorSidebar {...sidebar} />
                <ChapterEditor {...editorProps} />
            </div>
        </Tiptap>
    )
}