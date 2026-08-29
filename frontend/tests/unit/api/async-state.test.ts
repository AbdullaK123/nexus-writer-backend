import { describe, expect, test } from "vitest"
import type { UseQueryResult } from "@tanstack/react-query"
import { None, Ok, Some } from "oxide.ts"

import {
    isEmpty,
    resolveAsyncStates,
    toAsyncState,
    toOption,
} from "../../../src/infrastructure/api/utils"
import { ApiError } from "../../../src/shared/types"

function queryResult<T>(overrides: Partial<UseQueryResult<T, ApiError>>): UseQueryResult<T, ApiError> {
    return {
        isLoading: false,
        isPending: false,
        isError: false,
        data: undefined,
        error: null,
        ...overrides,
    } as UseQueryResult<T, ApiError>
}

describe("isEmpty", () => {
    test.each([null, undefined, "", [], {}, new Map(), new Set()])(
        "treats %j as empty",
        (value) => {
            expect(isEmpty(value)).toBe(true)
        },
    )

    test.each([0, false, "hello", [1], { id: 1 }, new Date()])(
        "does not treat %j as empty",
        (value) => {
            expect(isEmpty(value)).toBe(false)
        },
    )
})

describe("toAsyncState", () => {
    test("maps loading queries to loading", () => {
        expect(
            toAsyncState(queryResult({ isLoading: true, isPending: true })),
        ).toEqual({ status: "loading", data: None })
    })

    test("maps pending non-loading queries to idle", () => {
        expect(toAsyncState(queryResult({ isPending: true }))).toEqual({
            status: "idle",
            data: None,
        })
    })

    test("maps empty arrays to empty", () => {
        const state = toAsyncState(queryResult<[]>( { data: [] } ))

        expect(state.status).toBe("empty")
    })

    test("maps resolved data to success", () => {
        const state = toAsyncState(queryResult({ data: { id: "story-1" } }))

        expect(state.status).toBe("success")
        if (state.status === "success") {
            expect(state.data.unwrap().unwrap()).toEqual({ id: "story-1" })
        }
    })

    test("never converts an errored query into success", () => {
        const error = new ApiError(500, "boom")
        const query = queryResult({ isError: true, error })

        expect(() => toAsyncState(query)).toThrow(error)
    })
})

describe("resolveAsyncStates", () => {
    test("loading has priority over other unresolved states", () => {
        const result = resolveAsyncStates({
            story: { status: "idle", data: None },
            chapter: { status: "loading", data: None },
        })

        expect(result).toEqual({ status: "loading" })
    })

    test("empty wins after no state is loading", () => {
        const result = resolveAsyncStates({
            story: { status: "empty", data: Some(Ok([])) },
            chapter: { status: "success", data: Some(Ok({ id: "chapter-1" })) },
        })

        expect(result).toEqual({ status: "empty" })
    })

    test("idle is preserved when nothing is loading or empty", () => {
        const result = resolveAsyncStates({
            story: { status: "idle", data: None },
            chapter: { status: "success", data: Some(Ok({ id: "chapter-1" })) },
        })

        expect(result).toEqual({ status: "idle" })
    })

    test("combines successful data by key", () => {
        const result = resolveAsyncStates({
            story: { status: "success", data: Some(Ok({ id: "story-1" })) },
            chapter: { status: "success", data: Some(Ok({ id: "chapter-1" })) },
        })

        expect(result).toEqual({
            status: "success",
            data: {
                story: { id: "story-1" },
                chapter: { id: "chapter-1" },
            },
        })
    })
})

describe("toOption", () => {
    test("maps nullish values to None and preserves real values", () => {
        expect(toOption(null).isNone()).toBe(true)
        expect(toOption(undefined).isNone()).toBe(true)
        expect(toOption(0).unwrap()).toBe(0)
        expect(toOption(false).unwrap()).toBe(false)
    })
})
