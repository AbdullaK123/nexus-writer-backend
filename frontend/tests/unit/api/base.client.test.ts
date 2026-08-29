import { beforeEach, describe, expect, test, vi } from "vitest"
import { z } from "zod"

import { requestOptions } from "../../../src/infrastructure/api/types"
import {
    API_BASE_URL,
    jsonResponse,
    makeApiClient,
    makeFetchMock,
} from "../../helpers/http"

const ResponseSchema = z.object({
    value: z.string(),
})

const fetchMock = makeFetchMock()

beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal("fetch", fetchMock)
})

describe("ApiClient", () => {
    test("returns parsed data for a valid JSON response", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: "ok" }))

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isOk()).toBe(true)
        expect(result.unwrap()).toEqual({ value: "ok" })
    })

    test("fails when a successful JSON response violates its schema", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: 123 }))

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().message).toContain("value")
    })

    test.each([400, 401, 404, 422, 500])(
        "preserves HTTP status %i on server errors",
        async (status) => {
            fetchMock.mockResolvedValueOnce(
                jsonResponse({ detail: `status ${status}` }, status),
            )

            const result = await makeApiClient().getJson("resource", ResponseSchema)

            expect(result.isErr()).toBe(true)
            expect(result.unwrapErr().status).toBe(status)
            expect(result.unwrapErr().message).toBe(`status ${status}`)
        },
    )

    test("extracts nested FastAPI error messages", async () => {
        fetchMock.mockResolvedValueOnce(
            jsonResponse(
                { detail: { message: "Authentication required" } },
                401,
            ),
        )

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.unwrapErr().message).toBe("Authentication required")
    })

    test("fails when a JSON endpoint returns no content", async () => {
        fetchMock.mockResolvedValueOnce(new Response(null, { status: 204 }))

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().status).toBe(204)
    })

    test("fails when a successful response is not JSON", async () => {
        fetchMock.mockResolvedValueOnce(
            new Response("hello", {
                status: 200,
                headers: { "Content-Type": "text/plain" },
            }),
        )

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().message).toContain("Expected JSON")
    })

    test("maps network failures to ApiError", async () => {
        fetchMock.mockRejectedValueOnce(new TypeError("Failed to fetch"))

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().status).toBe(0)
        expect(result.unwrapErr().message).toBe("Network error")
    })

    test("maps aborted requests to ApiError without pretending they are HTTP failures", async () => {
        fetchMock.mockRejectedValueOnce(
            new DOMException("The operation was aborted", "AbortError"),
        )

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().status).toBe(0)
        expect(result.unwrapErr().message).toBe("Request was cancelled")
    })

    test("maps timeouts to request timeout", async () => {
        fetchMock.mockRejectedValueOnce(
            new DOMException("The operation timed out", "TimeoutError"),
        )

        const result = await makeApiClient().getJson("resource", ResponseSchema)

        expect(result.isErr()).toBe(true)
        expect(result.unwrapErr().status).toBe(408)
        expect(result.unwrapErr().message).toBe("Request timed out")
    })

    test("sends cookies and default JSON headers", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: "ok" }))

        await makeApiClient().getJson("resource", ResponseSchema)

        expect(fetchMock).toHaveBeenCalledWith(
            new URL("resource", API_BASE_URL).toString(),
            expect.objectContaining({
                method: "GET",
                credentials: "include",
                headers: expect.objectContaining({
                    Accept: "application/json",
                    "Content-Type": "application/json",
                }),
            }),
        )
    })

    test("merges caller headers without dropping defaults", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: "ok" }))

        await makeApiClient().getJson(
            "resource",
            ResponseSchema,
            requestOptions({ headers: { "X-Test": "yes" } }),
        )

        const options = fetchMock.mock.calls[0]?.[1]
        expect(options?.headers).toEqual(
            expect.objectContaining({
                Accept: "application/json",
                "Content-Type": "application/json",
                "X-Test": "yes",
            }),
        )
    })

    test.each([
        ["POST", "postJson"],
        ["PUT", "putJson"],
        ["PATCH", "patchJson"],
    ] as const)("%s serializes the request body as JSON", async (method, clientMethod) => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: "ok" }))
        const client = makeApiClient()
        const body = { title: "hello" }

        await client[clientMethod]("resource", body, ResponseSchema)

        expect(fetchMock).toHaveBeenCalledWith(
            new URL("resource", API_BASE_URL).toString(),
            expect.objectContaining({
                method,
                body: JSON.stringify(body),
            }),
        )
    })

    test("DELETE sends no request body", async () => {
        fetchMock.mockResolvedValueOnce(jsonResponse({ value: "ok" }))

        await makeApiClient().deleteJson("resource", ResponseSchema)

        const options = fetchMock.mock.calls[0]?.[1]
        expect(options?.method).toBe("DELETE")
        expect(options).toBeDefined()
        expect("body" in options!).toBe(false)
    })
})
