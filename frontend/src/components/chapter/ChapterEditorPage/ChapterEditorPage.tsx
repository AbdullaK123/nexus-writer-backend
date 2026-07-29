import { ChapterEditor } from "./ChapterEditor/ChapterEditor";
import { ChapterEditorSidebar } from "./ChapterEditorSidebar";
import { useChapterEditorPage } from "./useChapterEditorPage";
import styles from "./ChapterEditorPage.module.css"
import { Tiptap } from "@tiptap/react";
import { ChapterCommentsSidebar } from "./ChapterCommentsSidebar/ChapterCommentsSidebar";


export function ChapterEditorPage() {

    const { sidebar, editorProps, tipTapEditor, commentsSidebar } = useChapterEditorPage()

    return (
        <Tiptap editor={tipTapEditor}>
            <div className={styles['page-container']}>
                <ChapterEditorSidebar {...sidebar} />
                <ChapterEditor {...editorProps} />
                <ChapterCommentsSidebar {...commentsSidebar} />
            </div>
        </Tiptap>
    )
}