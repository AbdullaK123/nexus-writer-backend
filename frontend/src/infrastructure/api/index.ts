import {
    ApiClient,
    AuthClient,
    ChapterClient,
    ChatClient,
    StoryClient,
} from "./clients";
import type { AppConfig } from "../config"


export interface AppApi {
    auth: AuthClient
    story: StoryClient
    chapter: ChapterClient
    chat: ChatClient
}


/**
 * Build an `AppApi` instance bound to a concrete config.
 *
 * No module-level singleton — the api object is created at the
 * composition root (main.tsx) once config has been successfully
 * loaded, then handed to the React tree via `ApiProvider`.
 */
export function createApi(config: AppConfig): AppApi {
    const apiClient = new ApiClient(config)
    return Object.freeze({
        auth: new AuthClient(apiClient),
        story: new StoryClient(apiClient),
        chapter: new ChapterClient(apiClient),
        chat: new ChatClient(apiClient),
    })
}

