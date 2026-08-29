import { beforeEach, describe, expect, test, vi } from "vitest"
import { useQuery } from "@tanstack/react-query"

import { useApi } from "../../../src/data/providers/ApiProvider"
import { useCurrentUser } from "../../../src/data/queries/auth"
import { ApiError } from "../../../src/shared/types"

vi.mock("@tanstack/react-query", () => ({
    useQuery: vi.fn(),
    useMutation: vi.fn(),
    useQueryClient: vi.fn(),
}))

vi.mock("../../../src/data/providers/ApiProvider", () => ({
    useApi: vi.fn(),
}))

const user = {
    id: "user-1",
    username: "abdulla",
    email: "abdulla@example.com",
    profileImg: null,
    settings: {
        appearance: { theme: "system" as const, reduced_motion: false },
        editor: {
            font_family: "Literata",
            font_size: 18,
            line_height: 1.7,
            content_width: 760,
            spellcheck: true,
        },
        notifications: {
            analysis_ready: true,
            comments_ready: true,
            job_failures: true,
        },
    },
}

beforeEach(() => {
    vi.mocked(useApi).mockReturnValue({
        auth: {
            getCurrentUser: vi.fn(),
        },
    } as never)
})

describe("useCurrentUser", () => {
    test("maps a pending auth probe to loading", () => {
        vi.mocked(useQuery).mockReturnValue({ isPending: true } as never)

        expect(useCurrentUser()).toEqual({ status: "loading" })
    })

    test("maps 401 to unauthenticated instead of error", () => {
        vi.mocked(useQuery).mockReturnValue({
            isPending: false,
            isError: true,
            error: new ApiError(401, "Authentication required"),
        } as never)

        expect(useCurrentUser()).toEqual({ status: "unauthenticated" })
    })

    test("preserves non-auth failures as errors", () => {
        const error = new ApiError(500, "boom")
        vi.mocked(useQuery).mockReturnValue({
            isPending: false,
            isError: true,
            error,
        } as never)

        expect(useCurrentUser()).toEqual({ status: "error", error })
    })

    test("maps a resolved user to authenticated", () => {
        vi.mocked(useQuery).mockReturnValue({
            isPending: false,
            isError: false,
            data: user,
        } as never)

        expect(useCurrentUser()).toEqual({
            status: "authenticated",
            user,
        })
    })
})
