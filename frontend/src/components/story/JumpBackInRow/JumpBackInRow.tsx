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
                {chapterCards.map((card, idx) => (
                    <ChapterCard 
                        key={idx}
                        {...card}
                    />
                ))}
            </div>
        </div>
    )
}