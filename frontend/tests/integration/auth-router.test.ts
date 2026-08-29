import { describe, expect, test } from "vitest"
import { createMemoryHistory, createRouter } from "@tanstack/react-router"

import { routeTree } from "../../src/router"
import type { AuthContextValue } from "../../src/data/providers/AuthProvider/AuthContext"

function createAuthRouter(initialEntry: string, auth: AuthContextValue) {
    const history = createMemoryHistory({ initialEntries: [initialEntry] })
    return createRouter({
        routeTree,
        history,
        context: { auth },
    })
}

describe("app auth routing integration", () => {
    test("an unauthenticated protected URL redirects to login and preserves the original URL", async () => {
        const router = createAuthRouter("/login", { status: "unauthenticated" })

        await router.navigate({
            to: "/stories/$storyId/$chapterId",
            params: { storyId: "story-1", chapterId: "chapter-2" },
        })

        expect(router.state.location.pathname).toBe("/login")
        expect(router.state.location.search).toEqual({
            redirect: "/stories/story-1/chapter-2",
        })
    })

    test("the login route never redirects an unauthenticated user back to itself", async () => {
        const router = createAuthRouter(
            "/login?redirect=%2Fstories%2Fstory-1",
            { status: "unauthenticated" },
        )

        await router.load()

        expect(router.state.location.pathname).toBe("/login")
        expect(router.state.location.search).toEqual({
            redirect: "/stories/story-1",
        })
    })

    test("an authenticated user visiting login is redirected home", async () => {
        const router = createAuthRouter(
            "/signup",
            { status: "authenticated", user: {} as never },
        )

        await router.navigate({ to: "/login" })

        expect(router.state.location.pathname).toBe("/")
    })

    test("an authenticated protected URL remains on the requested resource", async () => {
        const router = createAuthRouter(
            "/login",
            { status: "authenticated", user: {} as never },
        )

        await router.navigate({
            to: "/stories/$storyId/$chapterId",
            params: { storyId: "story-1", chapterId: "chapter-2" },
        })

        expect(router.state.location.pathname).toBe("/stories/story-1/chapter-2")
    })
})
