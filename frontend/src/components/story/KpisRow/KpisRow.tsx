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
        <div className={styles['row-container']}>
            <span className="system-badge system-badge__nobg">
                [YOUR PROGRESS]
            </span>
            <div className={styles['kpis-container']}>
                <Card 
                    className="stat"
                    title="TOTAL WORDS"
                    footer={<p className="stat__caption">{`across ${storyCount} stories`}</p>}
                >
                    <h2 className="stat__value">{totalWords}</h2>
                </Card>
                <Card
                    className="stat"
                    title="CHAPTERS"
                    footer={<p className="stat__caption">{chaptersPublished}</p>}
                >
                    <h2 className="stat__value">{totalChapters}</h2>
                </Card>
                <Card
                    className="stat"
                    title="SCENES TRACKED"
                    footer={<p className="stat__caption">extracted</p>}
                >
                    <h2 className="stat__value">{totalScenesTracked}</h2>
                </Card>
                <Card
                    className="stat"
                    title="STREAK"
                    footer={<p className="stat__caption">days writing</p>}
                >
                    <h2 className="stat__value">{currentStreak}</h2>
                </Card>
            </div>
        </div>
    )
}