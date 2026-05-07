import { 
    ApiClient,
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

const apiClient = new ApiClient()

export const api: AppApi = Object.freeze({
    auth: new AuthClient(apiClient),
    story: new StoryClient(apiClient),
    chapter: new ChapterClient(apiClient),
    chat: new ChatClient(apiClient)
})

