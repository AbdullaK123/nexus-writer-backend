import { QueryCache, QueryClient } from "@tanstack/react-query"
import { createMemoryHistory, createRouter } from "@tanstack/react-router"
import { describe, expect, test } from "vitest"

import { routeTree } from "../../src/router"
import { routeQueryError } from "../../src/infrastructure/query-error-routing"
import { ApiError } from "../../src/shared/types"

function createHarness(initialEntry = "/stories/story-1") {
    const router = createRouter({
        routeTree,
        history: createMemoryHistory({ initialEntries: [initialEntry] }),
        context: { auth: { status: "authenticated", user: {} as never } },
    })

    let navigation: Promise<unknown> | undefined
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
        },
        queryCache: new QueryCache({
            onError: (error, query) => {
                routeQueryError(
                    error,
                    query.queryKey,
                    router.state.location.pathname,
                    (target) => {
                        navigation = router.navigate(target)
                        return navigation
                    },
                )
            },
        }),
    })

    return {
        router,
        queryClient,
        async waitForNavigation() {
            await navigation
        },
    }
}

async function runFailingQuery(
    queryClient: QueryClient,
    queryKey: readonly unknown[],
    error: Error,
) {
    await expect(
        queryClient.fetchQuery({
            queryKey,
            queryFn: async () => {
                throw error
            },
        }),
    ).rejects.toBe(error)
}

describe("query error navigation integration", () => {
    test("a protected query 401 navigates to login and preserves the failed route", async () => {
        const harness = createHarness()
        await harness.router.load()

        await runFailingQuery(
            harness.queryClient,
            ["stories", "detail", "story-1"],
            new ApiError(401, "Unauthorized"),
        )
        await harness.waitForNavigation()

        expect(harness.router.state.location.pathname).toBe("/login")
        expect(harness.router.state.location.search).toEqual({ redirect: "/stories/story-1" })
    })

    test("a 404 navigates to the not-found route", async () => {
        const harness = createHarness()
        await harness.router.load()

        await runFailingQuery(
            harness.queryClient,
            ["chapters", "detail", "missing"],
            new ApiError(404, "Not found"),
        )
        await harness.waitForNavigation()

        expect(harness.router.state.location.pathname).toBe("/404")
    })

    test("a server error navigates to the global error route", async () => {
        const harness = createHarness()
        await harness.router.load()

        await runFailingQuery(
            harness.queryClient,
            ["stories", "detail", "story-1"],
            new ApiError(500, "Boom"),
        )
        await harness.waitForNavigation()

        expect(harness.router.state.location.pathname).toBe("/error")
    })

    test("the auth probe 401 remains local and does not navigate", async () => {
        const harness = createHarness("/login")
        await harness.router.load()

        await runFailingQuery(
            harness.queryClient,
            ["auth", "me"],
            new ApiError(401, "Unauthorized"),
        )

        expect(harness.router.state.location.pathname).toBe("/login")
        expect(harness.router.state.location.search).toEqual({ redirect: undefined })
    })
})
