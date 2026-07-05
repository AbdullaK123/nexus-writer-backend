import {None, Option, Some} from "oxide.ts"
import { Button, LoadingSkeleton, ModalWithTrigger, Nothing } from "../../../../common";
import { SceneSearchPalette, type SceneSearchPaletteProps } from "../../../../story/SceneSearchPalette";
import styles from "./ChapterEditorFooter.module.css"
export type ChapterEditorFooterProps = 
| { status: "error" }
| { status: "empty" }
| { 
    status: "loading"
    searchPalette: SceneSearchPaletteProps
    onAskAgent: (query: string) => void
  }
| { 
    status: "ready",
    searchPalette: SceneSearchPaletteProps
    chapterNumber: number,
    prevChapterId: Option<string>,
    onClickPreviousChapter: Option<() => void>;
    nextChapterId: Option<string>,
    onClickNextChapter: Option<() => void>
    onNewChapter: (title: string) => void
    modalOpen: boolean
    onModalOpenChange: (e: boolean) => void
    newChapterTitle: string
    onNewChapterTitleChange: (title: string) => void
  }

export function ChapterEditorFooter(props: ChapterEditorFooterProps) {
    switch (props.status) {
        case "empty":
        case "error": {
            return <Nothing />
        }
        case "loading": {
            return (
                <div className={styles['content']}>
                    <LoadingSkeleton className={Some("btn btn--secondary")} />
                    <SceneSearchPalette
                        {...props.searchPalette}
                    />
                    <LoadingSkeleton className={Some("btn btn--secondary")} />
                </div>
            )
        }
        case "ready": {
            return (
                <div className={styles['content']}>
                    {props.prevChapterId.isSome() ? (
                        <Button
                            onClick={props.onClickPreviousChapter.isSome() ? props.onClickPreviousChapter.unwrap() : () => {}}
                            variant="secondary"
                        >
                           { `← CH ${props.chapterNumber - 1}`}
                        </Button>
                    ) : (
                        <div />
                    )}
                    <SceneSearchPalette
                        {...props.searchPalette}
                    />
                    {props.nextChapterId.isSome() ? (
                        <Button
                            onClick={props.onClickNextChapter.unwrap()}
                            variant="secondary"
                        >
                           { `CH ${props.chapterNumber + 1} →`}
                        </Button>
                    ): (
                         <ModalWithTrigger
                            open={props.modalOpen}
                            onOpenChange={props.onModalOpenChange}
                            closeTrigger={None}
                            title={None}
                            description={None}
                            content={
                            <div>
                                <h2>Create a new chapter</h2>
                                <div className="hstack">
                                <input
                                    type="text"
                                    value={props.newChapterTitle}
                                    className="field__input"
                                    placeholder="Give it a nice title..."
                                    onChange={(e) => props.onNewChapterTitleChange(e.target.value)}
                                    onKeyDown={(e) => {
                                        if (e.key === 'Enter') props.onNewChapter(props.newChapterTitle)
                                    }}
                                />
                                <Button variant="primary" onClick={() => props.onNewChapter(props.newChapterTitle)}>
                                    Submit
                                </Button>
                                </div>
                            </div>
                            }
                        >
                            <Button variant="primary">+ New Chapter</Button>
                        </ModalWithTrigger>
                    )}
                </div>
            )
        }
    }
}