import {Option, Some} from "oxide.ts"
import { Button, LoadingSkeleton } from "../../../../common";
import { SceneSearchPalette, type SceneSearchPaletteProps } from "../../../../story/SceneSearchPalette";

export type ChapterEditorFooterProps = 
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
    onClickPreviousChapter: () => void;
    nextChapterId: Option<string>,
    onClickNextChapter: () => void
  }

export function ChapterEditorFooter(props: ChapterEditorFooterProps) {
    switch (props.status) {
        case "loading": {
            return (
                <div>
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
                <div>
                    {props.prevChapterId.isSome() && (
                        <Button
                            onClick={props.onClickPreviousChapter}
                            variant="secondary"
                        >
                           { `← CH ${props.chapterNumber - 1}`}
                        </Button>
                    )}
                    <SceneSearchPalette
                        {...props.searchPalette}
                    />
                    {props.nextChapterId.isSome() && (
                        <Button
                            onClick={props.onClickNextChapter}
                            variant="secondary"
                        >
                           { `CH ${props.chapterNumber + 1} →`}
                        </Button>
                    )}
                </div>
            )
        }
    }
}