import { describe, expect, test, vi } from "vitest"

import { AuthClient } from "../../../src/infrastructure/api/clients/auth.client"
import { ChapterClient } from "../../../src/infrastructure/api/clients/chapter.client"
import { ChatClient } from "../../../src/infrastructure/api/clients/chat.client"
import { StoryClient } from "../../../src/infrastructure/api/clients/story.client"
import {
    ApiMessageSchema,
    ChapterContentResponseSchema,
    ChatMessageListResponseSchema,
    StoryDetailResponseSchema,
    ThreadResponseSchema,
    UserResponseSchema,
} from "../../../src/infrastructure/api/types"
import { makeApiClient } from "../../helpers/http"

function mockMethod<T extends object, K extends keyof T>(object: T, key: K) {
    return vi.spyOn(object, key as never).mockResolvedValue(undefined as never)
}

describe("domain API clients", () => {
    test("AuthClient probes the canonical current-user endpoint", () => {
        const api = makeApiClient()
        const getJson = mockMethod(api, "getJson")

        new AuthClient(api).getCurrentUser()

        expect(getJson).toHaveBeenCalledWith(
            "auth/me",
            UserResponseSchema,
            expect.any(Object),
        )
    })

    test("AuthClient sends login credentials to auth/login", () => {
        const api = makeApiClient()
        const postJson = mockMethod(api, "postJson")
        const payload = { email: "a@example.com", password: "secret" }

        new AuthClient(api).login(payload)

        expect(postJson).toHaveBeenCalledWith(
            "auth/login",
            payload,
            UserResponseSchema,
            expect.any(Object),
        )
    })

    test("StoryClient uses the story id in detail routes", () => {
        const api = makeApiClient()
        const getJson = mockMethod(api, "getJson")

        new StoryClient(api).getStoryDetails("story-1")

        expect(getJson).toHaveBeenCalledWith(
            "stories/story-1",
            StoryDetailResponseSchema,
            expect.any(Object),
        )
    })

    test("StoryClient sends chapter reorder positions without renaming them", () => {
        const api = makeApiClient()
        const postJson = mockMethod(api, "postJson")
        const payload = { fromPos: 4, toPos: 1 }

        new StoryClient(api).reorderChapters("story-1", payload)

        expect(postJson).toHaveBeenCalledWith(
            "stories/story-1/chapters/reorder",
            payload,
            ApiMessageSchema,
            expect.any(Object),
        )
    })

    test("StoryClient sends semantic-search filters to the story search endpoint", () => {
        const api = makeApiClient()
        const postJson = mockMethod(api, "postJson")
        const payload = {
            query: "harbor",
            k: 10,
            candidatePool: 50,
            tension: "high" as const,
            pacing: "fast" as const,
            tags: ["battle"],
            mentionedEntities: ["Mara"],
            chapterIds: ["chapter-1"],
        }

        new StoryClient(api).searchStoryScenes("story-1", payload)

        expect(postJson).toHaveBeenCalledWith(
            "stories/story-1/search",
            payload,
            expect.any(Object),
            expect.any(Object),
        )
    })

    test("ChapterClient preserves the as_html query parameter", () => {
        const api = makeApiClient()
        const getJson = mockMethod(api, "getJson")
        const client = new ChapterClient(api)

        client.getChapter("chapter-1", false)

        expect(getJson).toHaveBeenCalledWith(
            "chapters/chapter-1?as_html=false",
            ChapterContentResponseSchema,
            expect.any(Object),
        )
    })

    test("ChapterClient updates the selected chapter and returns chapter content", () => {
        const api = makeApiClient()
        const putJson = mockMethod(api, "putJson")
        const payload = { content: "<p>latest</p>" }

        new ChapterClient(api).updateChapter("chapter-7", payload)

        expect(putJson).toHaveBeenCalledWith(
            "chapters/chapter-7",
            payload,
            ChapterContentResponseSchema,
            expect.any(Object),
        )
    })

    test("ChatClient scopes message history by both story and thread", () => {
        const api = makeApiClient()
        const getJson = mockMethod(api, "getJson")

        new ChatClient(api).getThreadMessages("story-1", "thread-2")

        expect(getJson).toHaveBeenCalledWith(
            "stories/story-1/chat/threads/thread-2/messages",
            ChatMessageListResponseSchema,
            expect.any(Object),
        )
    })

    test("ChatClient createThread preserves the firstMessage wire field", () => {
        const api = makeApiClient()
        const postJson = mockMethod(api, "postJson")
        const payload = { firstMessage: "Help me with chapter one" }

        new ChatClient(api).createThread("story-1", payload)

        expect(postJson).toHaveBeenCalledWith(
            "stories/story-1/chat/threads",
            payload,
            ThreadResponseSchema,
            expect.any(Object),
        )
    })

    test("ChatClient renameThread targets only the selected thread", () => {
        const api = makeApiClient()
        const patchJson = mockMethod(api, "patchJson")
        const payload = { title: "New title" }

        new ChatClient(api).renameThread("story-1", "thread-2", payload)

        expect(patchJson).toHaveBeenCalledWith(
            "stories/story-1/chat/threads/thread-2",
            payload,
            ThreadResponseSchema,
            expect.any(Object),
        )
    })
})
