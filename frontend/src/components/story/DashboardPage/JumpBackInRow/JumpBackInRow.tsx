import { None, Some } from "oxide.ts";
import { EmptyState } from "../../../common";
import { ChapterCard, type ChapterCardProps } from "./ChapterCard/ChapterCard";
import styles from "./JumpBackInRow.module.css"


export type JumpBackInRowProps = {
    chapterCards: ChapterCardProps[]
}


export function JumpBackInRow({ chapterCards }: JumpBackInRowProps) {
    return (
        <div>
            <div className={styles['header']}>
                <span className="system-badge system-badge__nobg">[JUMP BACK IN]</span>
                <p>Last 3 chapters you touched</p>
            </div>
            <div className={styles['content']}>
                {chapterCards.length === 0 && (
                    <EmptyState 
                        headline="No Chapters."
                        title="No chapters yet."
                        description={Some("You haven't started writing any chapters yet. Click on any of your stories to start writing Chapter 1.")}
                        action={None}
                    />
                )}
                {chapterCards.length > 0 && (
                    chapterCards.map((card, idx) => (
                        <ChapterCard 
                            key={idx}
                            {...card}
                        />
                    ))
                )}
            </div>
        </div>
    )
}