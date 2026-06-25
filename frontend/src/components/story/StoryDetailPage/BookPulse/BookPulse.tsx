import type { PulseDimension } from "../../../../infrastructure/api/types";
import { Button } from "../../../common";
import styles from "./BookPulse.module.css"
export type BookPulseProps = {
    characters: PulseDimension,
    plot: PulseDimension,
    structure: PulseDimension,
    world: PulseDimension
}

export function BookPulse({
    characters,
    plot,
    structure,
    world
}: BookPulseProps) {

    const getLabelStyles = (label: "healthy" | "needs-attention" | "watch" | "unavailable") => {
        switch (label) {
            case "healthy": return styles['text-healthy']
            case "needs-attention": return styles['text-warn']
            case "unavailable": return styles['text-not-available']
            case "watch": return styles['text-needs-attention']
        }
    }

    const getLabelText = (label: "healthy" | "needs-attention" | "watch" | "unavailable") => {
        switch (label) {
            case "healthy": return "healthy"
            case "needs-attention": return "needs attention"
            case "unavailable": return "not available"
            case "watch": return "watch"
        }
    }


    return (
        <div>
            <div>
                <div>
                    <span className="system-badge system-badge__nobg">
                        [BOOK PULSE]
                    </span>
                    <p>From the analytics agent</p>
                </div>
                <Button
                    variant="ghost"
                    onClick={() => {}}
                >
                    → FULL
                </Button>
            </div>
            <div className={styles['content']}>
                <div className={styles['pulse-card']}>
                    <div className={styles['pulse-card-header']}>
                        <p className={styles['all-caps']}>CHARACTERS</p>
                        <p className={getLabelStyles(characters.label)}>
                            {getLabelText(characters.label)}
                        </p>
                    </div>
                    <h3>{characters.headline}</h3>
                    <p>{characters.report}</p>
                </div>
                <div className={styles['pulse-card']}>
                    <div className={styles['pulse-card-header']}>
                        <p className={styles['all-caps']}>PLOT</p>
                        <p className={getLabelStyles(plot.label)}>
                            {getLabelText(plot.label)}
                        </p>
                    </div>
                    <h3>{plot.headline}</h3>
                    <p>{plot.report}</p>
                </div>
                <div className={styles['pulse-card']}>
                    <div className={styles['pulse-card-header']}>
                        <p className={styles['all-caps']}>STRUCTURE</p>
                        <p className={getLabelStyles(structure.label)}>
                            {getLabelText(structure.label)}
                        </p>
                    </div>
                    <h3>{structure.headline}</h3>
                    <p>{structure.report}</p>
                </div>
                <div className={styles['pulse-card']}>
                    <div className={styles['pulse-card-header']}>
                        <p className={styles['all-caps']}>WORLD</p>
                        <p className={getLabelStyles(world.label)}>
                            {getLabelText(world.label)}
                        </p>
                    </div>
                    <h3>{world.headline}</h3>
                    <p>{world.report}</p>
                </div>
            </div>
        </div>
    )
}