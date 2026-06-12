import { useState } from "react";
import { BeginNewStoryCard } from "./BeginNewStoryCard";
import { FilterChip } from "./FilterChip/FilterChip";
import { StoryCard, type StoryCardProps } from "./StoryCard/StoryCard";
import { toStatusBadgeVariant } from "./StoryCard";
import styles from './LibraryGrid.module.css'



export type LibraryGridProps = {
    stories: StoryCardProps[]
    onNewStory: () => void;
}

const getCounts = (stories: StoryCardProps[]) => {
    const allCount = stories.length
    const ongoingCount = stories.filter((story) => story.status === "Ongoing").length
    const hiatusCount = stories.filter((story) => story.status === "On Hiatus").length
    const completeCount = stories.filter((story) => story.status === "Complete").length
    return {
        all: allCount,
        ongoing: ongoingCount,
        hiatus: hiatusCount,
        complete: completeCount
    }
}

export function LibraryGrid({ stories, onNewStory }: LibraryGridProps) {
    
    const [selected, setSelected] = useState< "all" | "ongoing" | "hiatus" | "complete">("all")

    const counts = getCounts(stories)

    return (
        <div className={styles['main-container']}>
            <div className={styles['header']}>
                <div className={styles['header__title']}>
                    <span className="system-badge system-badge__nobg">{`[STORIES - ${stories.length}]`}</span>
                    <h2>Your Library</h2>
                </div>
                <div className={styles['header__filters']}>
                    <FilterChip 
                        status="all"
                        count={counts.all}
                        selected={selected === "all"}
                        onClick={() => setSelected("all")}
                    />
                    <FilterChip 
                        status="ongoing"
                        count={counts.ongoing}
                        selected={selected === "ongoing"}
                        onClick={() => setSelected("ongoing")}
                    />
                    <FilterChip 
                        status="hiatus"
                        count={counts.hiatus}
                        selected={selected === "hiatus"}
                        onClick={() => setSelected("hiatus")}
                    />
                    <FilterChip 
                        status="complete"
                        count={counts.complete}
                        selected={selected === "complete"}
                        onClick={() => setSelected("complete")}
                    />
                </div>
            </div>
            <div className={styles['content']}>
                {stories.length > 0 && (
                    stories.filter((story) => {
                        if (selected === "all") 
                            return true 
                        else
                            return toStatusBadgeVariant(story.status) === selected

                    }).map((story, idx) =>(
                        <StoryCard 
                            key={idx}
                            {...story}
                        />
                    ))
                )}
                <BeginNewStoryCard onClick={onNewStory} />
            </div>
        </div>
    )
}