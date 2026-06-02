import { Card } from "../../common"
import styles from "./KpisRow.module.css"


type KpisRowProps = {
    totalWords: number
    storyCount: number 
    totalChapters: number 
    chaptersPublished: number
    totalScenesTracked: number 
    currentStreak: number 
}

export function KpisRow({
    totalWords,
    storyCount,
    totalChapters,
    chaptersPublished,
    totalScenesTracked,
    currentStreak
}: KpisRowProps) {
    return (
        <div>
            <span className="system-badge system-badge__nobg">
                [YOUR PROGRESS]
            </span>
            <div className={styles['kpis-container']}>
                <Card 
                    title="TOTAL WORDS"
                    footer={`across ${storyCount} stories`}
                >
                    <h2>{totalWords}</h2>
                </Card>
                <Card
                    title="CHAPTERS"
                    footer={`${chaptersPublished}`}
                >
                    <h2>{totalChapters}</h2>
                </Card>
                <Card
                    title="SCENES TRACKED"
                    footer="extracted"
                >
                    <h2>{totalScenesTracked}</h2>
                </Card>
                <Card
                    title="STREAK"
                    footer="days writing"
                >
                    <h2>{currentStreak}</h2>
                </Card>
            </div>
        </div>
    )
}