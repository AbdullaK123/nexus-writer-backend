import { Button } from "../Button";
import { router } from "../../../router"
import styles from "./NotFoundPage.module.css"

export function NotFoundPage() {
    return (
        <div className={styles['content-container']}>
            <div className={styles['content']}>
                <span className={styles['logo']}>404</span>
                <span className={`system-badge system-badge__nobg`}>
                    {`[NOT FOUND]`}
                </span>
                <p className={styles['red-text']}>Whoops. That page does not exist.</p>
                <Button
                    variant="primary"
                    onClick={() => router.navigate({ to: "/" })}
                >
                    Go back to dashboard
                </Button>
            </div>
        </div>
    )
}