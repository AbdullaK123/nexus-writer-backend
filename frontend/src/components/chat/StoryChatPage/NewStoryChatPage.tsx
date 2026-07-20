import { StoryChatSidebar } from "./StoryChatSidebar";
import { ChatComposer } from "./StoryChatWindow/ChatComposer/ChatComposer";
import { useNewStoryChatPage } from "./useNewStoryChatPage";
import styles from "./StoryChatPage.module.css"

export function NewStoryChatPage() {

    const { sidebar, composer } = useNewStoryChatPage()

    return (
        <div className={styles['page-container']}>
            <StoryChatSidebar {...sidebar} />
            <div className={`${styles['content-container']} ${styles['centered']}`}>
                <div className="flex-col">
                    <h2 className={styles['text-centered']}>Let's talk about your book</h2>
                    <ChatComposer {...composer} />
                </div>
            </div>
        </div>
    )
}