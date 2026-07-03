import { ChapterEditorContent, type ChapterEditorContentProps } from "./ChapterEditorContent";
import { ChapterEditorFooter, type ChapterEditorFooterProps } from "./ChapterEditorFooter";
import { ChapterEditorHeader, type ChapterEditorHeaderProps } from "./ChapterEditorHeader";
import styles from "./ChapterEditor.module.css"


export type ChapterEditorProps = {
    header: ChapterEditorHeaderProps
    content: ChapterEditorContentProps
    footer: ChapterEditorFooterProps
}

export function ChapterEditor(props: ChapterEditorProps) {
    return (
        <div className={styles['content']}>
            <ChapterEditorHeader {...props.header} />
            <ChapterEditorContent {...props.content} />
            <ChapterEditorFooter {...props.footer} />
        </div>
    )
}