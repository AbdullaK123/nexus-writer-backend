import { None, Some } from "oxide.ts";
import { Card } from "../../../common"
import styles from "./KpisRow.module.css"


export type KpisRowProps = {
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
                    cardTitle={None}
                    subtitle={None}
                    header={Some("TOTAL WORDS")}
                    footer={Some(<p className="stat__caption">{`across ${storyCount} stories`}</p>)}
                >
                    <h2 className="stat__value">{totalWords}</h2>
                </Card>
                <Card
                    className="stat"
                    cardTitle={None}
                    subtitle={None}
                    header={Some("CHAPTERS")}
                    footer={Some(<p className="stat__caption">{chaptersPublished} published</p>)}
                >
                    <h2 className="stat__value">{totalChapters}</h2>
                </Card>
                <Card
                    className="stat"
                    cardTitle={None}
                    subtitle={None}
                    header={Some("SCENES TRACKED")}
                    footer={Some(<p className="stat__caption">extracted</p>)}
                >
                    <h2 className="stat__value">{totalScenesTracked}</h2>
                </Card>
                <Card
                    className="stat"
                    cardTitle={None}
                    subtitle={None}
                    header={Some("STREAK")}
                    footer={Some(<p className="stat__caption">days writing</p>)}
                >
                    <h2 className="stat__value">{currentStreak}</h2>
                </Card>
            </div>
        </div>
    )
}