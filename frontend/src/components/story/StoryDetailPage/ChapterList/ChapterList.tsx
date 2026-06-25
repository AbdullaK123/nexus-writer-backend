import { None, Some } from "oxide.ts";
import { Button, EmptyState } from "../../../common";
import { ChapterListFilterBar, type ChapterListFilterBarProps } from "./ChapterListFilterBar/ChapterListFilterBar";
import { ChapterListItem, type ChapterListItemProps } from "./ChapterListItem/ChapterListItem";
import styles from "./ChapterList.module.css"

export type ChapterListProps = {
    filterBar: ChapterListFilterBarProps,
    chapterListItems: ChapterListItemProps[]
}

export function ChapterList({
    filterBar,
    chapterListItems
}: ChapterListProps) {
    return (
        <div className={styles['content']}>
            <ChapterListFilterBar 
                {...filterBar}
            />
            {chapterListItems.length === 0 && (
                <EmptyState 
                    headline="No chapters yet"
                    title="Start chapter 1?"
                    description={None}
                    action={Some(
                        <Button
                            variant="primary"
                        >
                            Take me to the editor
                        </Button>
                    )}
                />
            )}
            <div className={styles['list-items']}>
                {chapterListItems.map((item, idx) => (
                    <ChapterListItem 
                        key={idx}
                        {...item}
                    />
                ))}
            </div>
        </div>
    )
}

