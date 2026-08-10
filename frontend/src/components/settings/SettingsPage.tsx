import { AppearanceSettings } from "./AppearanceSettings";
import { EditorSettings } from "./EditorSettings";
import { NotificationSettings } from "./NotificationSettings";
import styles from "./SettingsPage.module.css"


export function SettingsPage() {
    return (
        <div className={styles['content']}>
            <span className="system-badge system-badge__nobg">
                [APP SETTINGS]
            </span>
            <AppearanceSettings />
            <EditorSettings />
            <NotificationSettings />
        </div>
    )
}