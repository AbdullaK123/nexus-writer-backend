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
            <div className={styles['space-between']}>
                 <span className="system-badge system-badge__nobg">
                    [YOUR PROGRESS]
                </span>
                <p>{`${currentStreak} day streak`}</p>
            </div>
            <div className={styles['kpis-container']}>
                <Card 
                    className="stat"
                    header="TOTAL WORDS"
                    footer={<p className="stat__caption">{`across ${storyCount} stories`}</p>}
                >
                    <h2 className="stat__value">{totalWords}</h2>
                </Card>
                <Card
                    className="stat"
                    header="CHAPTERS"
                    footer={<p className="stat__caption">{chaptersPublished} published</p>}
                >
                    <h2 className="stat__value">{totalChapters}</h2>
                </Card>
                <Card
                    className="stat"
                    header="SCENES TRACKED"
                    footer={<p className="stat__caption">extracted</p>}
                >
                    <h2 className="stat__value">{totalScenesTracked}</h2>
                </Card>
                <Card
                    className="stat"
                    header="STREAK"
                    footer={<p className="stat__caption">days writing</p>}
                >
                    <h2 className="stat__value">{currentStreak}</h2>
                </Card>
            </div>
        </div>
    )
}