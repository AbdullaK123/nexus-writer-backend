import { FilterChip } from "../../../DashboardPage/LibraryGrid/FilterChip/FilterChip";
import { Option } from "oxide.ts"
import styles from "./ChapterListFilterBar.module.css"

export type ChapterListFilterBarProps = {
    totalChapters: number
    totalDraftChapters: number 
    totalPublishedChapters: number
    onClickFilterChip: () => void;
    selectedFilter: Option<"all" | "draft" | "published">
}

export function ChapterListFilterBar({
    totalChapters,
    totalDraftChapters,
    totalPublishedChapters,
    onClickFilterChip,
    selectedFilter
}: ChapterListFilterBarProps) {
    return (
        <div className={styles['main-content']}>
            <div className={styles['count-container']}>
                <span className="system-badge system-badge__nobg">
                    {`[CHAPTERS - ${totalChapters}]`}
                </span>
                <p>Most recent first</p>
            </div>
            <div className={styles['filter-chip-container']}>
                <FilterChip 
                    status="all"
                    count={totalChapters}
                    selected={selectedFilter.isSome() ? selectedFilter.unwrap() === "all" : true}
                    onClick={onClickFilterChip}
                />
                <FilterChip 
                    status="draft"
                    count={totalDraftChapters}
                    selected={selectedFilter.isSome() ? selectedFilter.unwrap() === "draft" : false}
                    onClick={onClickFilterChip}
                />
                <FilterChip 
                    status="published"
                    count={totalPublishedChapters}
                    selected={selectedFilter.isSome() ? selectedFilter.unwrap() === "published" : false}
                    onClick={onClickFilterChip}
                />
            </div>
        </div>
    )
}