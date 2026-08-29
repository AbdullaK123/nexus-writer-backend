import { describe, expect, test } from "vitest"

import {
    noRequestOptions,
    requestOptions,
} from "../../../src/infrastructure/api/types"

describe("requestOptions", () => {
    test("wraps an AbortSignal when provided", () => {
        const controller = new AbortController()

        const options = requestOptions({ signal: controller.signal })

        expect(options.signal.isSome()).toBe(true)
        expect(options.signal.unwrap()).toBe(controller.signal)
    })

    test("keeps omitted values as None", () => {
        const options = requestOptions()

        expect(options.signal.isNone()).toBe(true)
        expect(options.timeoutMs.isNone()).toBe(true)
        expect(options.headers.isNone()).toBe(true)
    })

    test("does not turn explicit null into a value", () => {
        const options = requestOptions({
            signal: null,
            timeoutMs: null,
            headers: null,
        })

        expect(options.signal.isNone()).toBe(true)
        expect(options.timeoutMs.isNone()).toBe(true)
        expect(options.headers.isNone()).toBe(true)
    })

    test("preserves a caller timeout override", () => {
        const options = requestOptions({ timeoutMs: 250 })

        expect(options.timeoutMs.unwrap()).toBe(250)
    })

    test("preserves caller headers exactly", () => {
        const headers = {
            "X-Correlation-ID": "request-1",
            Authorization: "Bearer token",
        }

        const options = requestOptions({ headers })

        expect(options.headers.unwrap()).toEqual(headers)
    })
})

describe("noRequestOptions", () => {
    test("contains no implicit signal, timeout, or headers", () => {
        expect(noRequestOptions.signal.isNone()).toBe(true)
        expect(noRequestOptions.timeoutMs.isNone()).toBe(true)
        expect(noRequestOptions.headers.isNone()).toBe(true)
    })
})
