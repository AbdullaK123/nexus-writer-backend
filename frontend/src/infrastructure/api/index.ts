import { 
    AuthClient, 
    ChapterClient, 
    ChatClient, 
    StoryClient
 } from "./clients";


export interface AppApi {
    auth: AuthClient
    story: StoryClient
    chapter: ChapterClient
    chat: ChatClient
}


export const api: AppApi = Object.freeze({
    auth: new AuthClient(),
    story: new StoryClient(),
    chapter: new ChapterClient(),
    chat: new ChatClient()
})

