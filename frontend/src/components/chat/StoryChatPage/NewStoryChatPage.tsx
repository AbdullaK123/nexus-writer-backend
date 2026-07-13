import { StoryChatSidebar } from "./StoryChatSidebar";
import { ChatComposer } from "./StoryChatWindow/ChatComposer/ChatComposer";
import { useNewStoryChatPage } from "./useNewStoryChatPage";

export function NewStoryChatPage() {

    const { sidebar, composer } = useNewStoryChatPage()

    return (
        <div>
            <StoryChatSidebar {...sidebar} />
            <div>
                <div>
                    <h2>Let's talk about your book</h2>
                    <ChatComposer {...composer} />
                </div>
            </div>
        </div>
    )
}