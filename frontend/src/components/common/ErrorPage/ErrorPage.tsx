import { Button } from "../Button";
import styles from "./ErrorPage.module.css"
import { errorRoute, router } from "../../../router"

export function ErrorPage() {

    const { redirect } = errorRoute.useSearch()

    return (
        <div className={styles['content-container']}>
            <div className={styles['content']}>
                <span className={styles['logo']}>!</span>
                <span className={`system-badge system-badge__nobg ${styles['red-text']}`}>
                    {`[ERROR]`}
                </span>
                <p className={styles['red-text']}>Something went wrong. The server might be experiencing issues.</p>
                <Button
                    variant="primary"
                    onClick={() => router.navigate({ to: redirect })}
                >
                    Try Again
                </Button>
            </div>
        </div>
    )
}