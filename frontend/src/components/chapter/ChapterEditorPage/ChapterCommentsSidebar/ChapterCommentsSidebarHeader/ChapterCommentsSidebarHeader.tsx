import type { CommentCategory } from "../../../../../infrastructure/api/types";
import { PanelRightOpen, PanelRightClose } from "lucide-react"
import { FilterChipNoCounts } from "../../../../story/DashboardPage/LibraryGrid/FilterChip/FilterChip";
import styles from "./ChapterCommentsSidebarHeader.module.css"
import { Button } from "../../../../common";
import type { DismissedComment } from "../useChapterCommentsSidebarProps";

export type FilterCounts = 
{
    all: number
    character: number
    continuity: number
    clarity: number
    plot: number
    structure: number
    pacing: number
    dialogue: number
    worldbuilding: number
    prose: number
}


export type ChapterCommentsSidebarHeaderProps = 
{
    activeCategory: CommentCategory | "all"
    filterCounts: FilterCounts
    view: "active" | "dismissed"
    onViewChange: (view: "active" | "dismissed") => void
    dismissedKeys: DismissedComment[]
    sidebarOpen: boolean
    onSidebarOpenChange: (e: boolean) => void
    onClickAll: () => void
    onClickCharacter: () => void
    onClickContinuity: () => void
    onClickClarity: () => void
    onClickPlot: () => void
    onClickStructure: () => void
    onClickPacing: () => void
    onClickDialogue: () => void
    onClickWorld: () => void
    onClickProse: () => void
}

const getActiveCount = (category: CommentCategory | "all", counts: FilterCounts, dismissedComments: DismissedComment[]) => {
    switch (category) {
        case "all":
            return counts.all - dismissedComments.length
        case "character":
            return counts.character > 0 ? counts.character - dismissedComments.filter((comment) => comment.category === "character").length : 0
        case "clarity":
            return counts.clarity > 0 ? counts.clarity - dismissedComments.filter((comment) => comment.category === "clarity").length : 0
        case "continuity":
            return counts.continuity > 0 ? counts.continuity - dismissedComments.filter((comment) => comment.category === "continuity").length : 0
        case "dialogue":
            return counts.dialogue > 0 ? counts.dialogue - dismissedComments.filter((comment) => comment.category === "dialogue").length : 0
        case "not-available":
            return 0
        case "pacing":
            return counts.pacing > 0 ? counts.character - dismissedComments.filter((comment) => comment.category === "pacing").length : 0
        case "plot":
            return counts.plot > 0 ? counts.plot - dismissedComments.filter((comment) => comment.category === "plot").length : 0
        case "prose":
            return counts.prose > 0 ? counts.prose - dismissedComments.filter((comment) => comment.category === "prose").length : 0
        case "structure":
            return counts.structure > 0 ? counts.structure - dismissedComments.filter((comment) => comment.category === "structure").length : 0
        case "worldbuilding":
            return counts.worldbuilding > 0 ? counts.worldbuilding - dismissedComments.filter((comment) => comment.category === "worldbuilding").length : 0
    }
}

export function ChapterCommentsSidebarHeader(props: ChapterCommentsSidebarHeaderProps) {
    return (
        <div className={`${styles['content']} ${props.sidebarOpen ? "" : styles['closed']}`}>
            <div className={styles['content']}>
                <span className="system-badge system-badge__nobg">
                    [COMMENTS]
                </span>
                <div className={styles['header']}>
                    <Button
                        variant="ghost"
                        className={styles['icon-btn']}
                        onClick={() => props.onSidebarOpenChange(props.sidebarOpen)}
                    >
                        {props.sidebarOpen ? (
                            <PanelRightClose 
                                color={"#ffffff"}
                                width={24}
                                height={24}
                            />
                        ): (
                            <PanelRightOpen 
                                color={"#ffffff"}
                                width={24}
                                height={24}
                            />
                        )}
                    </Button>
                    <span className={styles['counts']}>
                        {`${getActiveCount(props.activeCategory, props.filterCounts, props.dismissedKeys)} active`}
                    </span>
                    <span className={styles['counts']}>
                        {`${props.dismissedKeys.filter((comment) => {
                            if (props.activeCategory === "all") {
                                return true
                            } else {
                                return props.activeCategory === comment.category
                            }
                        }).length} dismissed`}
                    </span>
                </div>
            </div>
            <div className={styles['content']}>
                <span className="system-badge system-badge__nobg">
                    [VIEW]
                </span>
                <div className={styles['header']}>
                    <FilterChipNoCounts 
                        label="active"
                        status={(props.view === "active") ? "selected": "idle"}
                        onClick={() => props.onViewChange("active")}
                    />
                    <FilterChipNoCounts 
                        label="dismissed"
                        status={(props.view === "dismissed") ? "selected": "idle"}
                        onClick={() => props.onViewChange("dismissed")}
                    />
                </div>
            </div>
            <div className={styles['content']}>
                <span className="system-badge system-badge__nobg">
                    [FILTERS]
                </span>
                <div className={styles['filter-actions']}>
                    <FilterChipNoCounts
                        label="all"
                        status={(props.activeCategory === "all") ? "selected" : "idle"}
                        onClick={props.onClickAll}
                    />
                    <FilterChipNoCounts
                        label="character"
                        status={(props.activeCategory === "character") ? "selected" : "idle"}
                        onClick={props.onClickCharacter}
                    />
                    <FilterChipNoCounts
                        label="continuity"
                        status={(props.activeCategory === "continuity") ? "selected" : "idle"}
                        onClick={props.onClickContinuity}
                    />
                    <FilterChipNoCounts
                        label="clarity"
                        status={(props.activeCategory === "clarity") ? "selected" : "idle"}
                        onClick={props.onClickClarity}
                    />
                    <FilterChipNoCounts
                        label="plot"
                        status={(props.activeCategory === "plot") ? "selected" : "idle"}
                        onClick={props.onClickPlot}
                    />
                    <FilterChipNoCounts
                        label="structure"
                        status={(props.activeCategory === "structure") ? "selected" : "idle"}
                        onClick={props.onClickStructure}
                    />
                    <FilterChipNoCounts
                        label="pacing"
                        status={(props.activeCategory === "pacing") ? "selected" : "idle"}
                        onClick={props.onClickPacing}
                    />
                    <FilterChipNoCounts
                        label="dialogue"
                        status={(props.activeCategory === "dialogue") ? "selected" : "idle"}
                        onClick={props.onClickDialogue}
                    />
                    <FilterChipNoCounts
                        label="world"
                        status={(props.activeCategory === "worldbuilding") ? "selected" : "idle"}
                        onClick={props.onClickWorld}
                    />
                    <FilterChipNoCounts
                        label="prose"
                        status={(props.activeCategory === "prose") ? "selected" : "idle"}
                        onClick={props.onClickProse}
                    />
                </div>
            </div>
        </div>
    )
}