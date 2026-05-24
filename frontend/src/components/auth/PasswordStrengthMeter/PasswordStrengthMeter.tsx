import styles from "./PasswordStrengthMeter.module.css"

type PasswordStrengthMeterProps = {
    score: number
    suggestions: string[]
}

export function PasswordStrengthMeter({ score, suggestions }: PasswordStrengthMeterProps) {
    return (
        <>
            <div className={styles['bars']}>
                {Array.from({ length: 4}, (_, i) => (
                    <div key={i} className={ (i < score ) ?  `${styles['progress-bar']} ${styles['filled']}` : `${styles['progress-bar']}` } />
                ))}
            </div>
            {suggestions.map((suggestion, i) => (
                <p key={i} className={styles['suggestion']}>{suggestion}</p>
            ))}
        </>
    )
}