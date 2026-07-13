import { StoryChatHeader } from "./StoryChatHeader";
import { StoryChatSidebar } from "./StoryChatSidebar";
import { StoryChatWindow } from "./StoryChatWindow";
import { useStoryChatPage } from "./useStoryChatPage";
import styles from "./StoryChatPage.module.css"

export function StoryChatPage() {

    const { header, sidebar, window } = useStoryChatPage()

    return (
        <div className={styles['page-container']}>
            <StoryChatSidebar {...sidebar} />
            <div className={styles['content-container']}>
                <StoryChatHeader {...header} />
                <StoryChatWindow {...window} />
            </div>
        </div>
    )
}