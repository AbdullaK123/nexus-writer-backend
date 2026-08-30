export type ChapterContentHydrator = {
    commands: {
        setContent: (
            content: string,
            options?: { emitUpdate?: boolean },
        ) => boolean
    }
}

export function hydrateChapterContent(
    editor: ChapterContentHydrator,
    content: string,
): void {
    editor.commands.setContent(content, { emitUpdate: false })
}
