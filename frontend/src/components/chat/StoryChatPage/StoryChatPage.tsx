import { StoryChatHeader } from "./StoryChatHeader";
import { StoryChatSidebar } from "./StoryChatSidebar";
import { StoryChatWindow } from "./StoryChatWindow";
import { useStoryChatPage } from "./useStoryChatPage";

export function StoryChatPage() {

    const { header, sidebar, window } = useStoryChatPage()

    return (
        <div>
            <StoryChatSidebar {...sidebar} />
            <div>
                <StoryChatHeader {...header} />
                <StoryChatWindow {...window} />
            </div>
        </div>
    )
}