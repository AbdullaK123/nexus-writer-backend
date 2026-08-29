import { vi } from "vitest"

import type { AppConfig } from "../../src/infrastructure/config"
import { ApiClient } from "../../src/infrastructure/api/clients/base.client"

export const API_BASE_URL = "http://api.test/"

export function makeApiClient(): ApiClient {
    const config: AppConfig = {
        api: {
            baseURL: API_BASE_URL,
            defaultTimeoutMs: 5_000,
        },
        mode: "test",
        isDev: false,
        isProd: false,
    }

    return new ApiClient(config)
}

export function makeFetchMock() {
    return vi.fn<typeof fetch>()
}

export function jsonResponse(body: unknown, status = 200): Response {
    return new Response(JSON.stringify(body), {
        status,
        headers: {
            "Content-Type": "application/json",
        },
    })
}
