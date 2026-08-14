import { AppearanceSettings } from "./AppearanceSettings";
import { EditorSettings } from "./EditorSettings";
import { NotificationSettings } from "./NotificationSettings";
import styles from "./SettingsPage.module.css"


export function SettingsPage() {
    return (
        <div className={styles['content']}>
            <h2>App Settings</h2>
            <AppearanceSettings />
            <EditorSettings />
            <NotificationSettings />
        </div>
    )
}