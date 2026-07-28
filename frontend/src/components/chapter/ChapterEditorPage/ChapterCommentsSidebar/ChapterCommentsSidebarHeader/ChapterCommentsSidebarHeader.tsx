import type { CommentCategory } from "../../../../../infrastructure/api/types";
import { PanelRightOpen, PanelRightClose } from "lucide-react"
import { FilterChipNoCounts } from "../../../../story/DashboardPage/LibraryGrid/FilterChip/FilterChip";
import styles from "./ChapterCommentsSidebarHeader.module.css"
import { Button } from "../../../../common";

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
    world: number
    prose: number
}


export type ChapterCommentsSidebarHeaderProps = 
{
    activeCategory: CommentCategory | "all"
    filterCounts: FilterCounts
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

const getActiveCount = (category: CommentCategory | "all", counts: FilterCounts) => {
    switch (category) {
        case "all":
            return counts.all
        case "character":
            return counts.character
        case "clarity":
            return counts.clarity
        case "continuity":
            return counts.continuity
        case "dialogue":
            return counts.dialogue
        case "not-available":
            return 0
        case "pacing":
            return counts.pacing
        case "plot":
            return counts.plot
        case "prose":
            return counts.prose
        case "structure":
            return counts.structure
        case "worldbuilding":
            return counts.world
    }
}

export function ChapterCommentsSidebarHeader(props: ChapterCommentsSidebarHeaderProps) {
    return (
        <div className={`${styles['content']} ${props.sidebarOpen ? "" : styles['closed']}`}>
            <div className={styles['header']}>
                <span className="system-badge system-badge__nobg">
                    [COMMENTS]
                </span>
                <span className={styles['counts']}>
                    {`${getActiveCount(props.activeCategory, props.filterCounts)} active`}
                </span>
                <Button
                    variant="ghost"
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
            </div>
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
    )
}