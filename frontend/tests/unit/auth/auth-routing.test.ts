import { describe, expect, test } from "vitest"

import {
    decideAppAuthRoute,
    decideLoginAuthRoute,
} from "../../../src/infrastructure/auth-routing"
import { ApiError } from "../../../src/shared/types"

const authenticated = {
    status: "authenticated" as const,
    user: {
        id: "user-1",
        username: "abdulla",
        email: "a@example.com",
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
    },
}

describe("app auth routing", () => {
    test("allows authenticated users", () => {
        expect(decideAppAuthRoute(authenticated, "/stories/story-1")).toEqual({
            kind: "allow",
        })
    })

    test("allows loading auth state to resolve without redirecting", () => {
        expect(decideAppAuthRoute({ status: "loading" }, "/stories/story-1")).toEqual({
            kind: "allow",
        })
    })

    test("redirects unauthenticated users and preserves the full origin", () => {
        expect(
            decideAppAuthRoute(
                { status: "unauthenticated" },
                "/stories/story-1/chat/thread-2?prompt=hello",
            ),
        ).toEqual({
            kind: "redirect-login",
            redirect: "/stories/story-1/chat/thread-2?prompt=hello",
        })
    })

    test("does not allow an auth error into protected routes", () => {
        expect(
            decideAppAuthRoute(
                { status: "error", error: new ApiError(500, "boom") },
                "/settings",
            ),
        ).toEqual({ kind: "redirect-login", redirect: "/settings" })
    })
})

describe("login auth routing", () => {
    test("authenticated users leave login for home", () => {
        expect(decideLoginAuthRoute(authenticated)).toEqual({
            kind: "redirect-home",
        })
    })

    test.each([
        { status: "loading" as const },
        { status: "unauthenticated" as const },
        { status: "error" as const, error: new ApiError(500, "boom") },
    ])("never redirects a non-authenticated login state back to login", (auth) => {
        expect(decideLoginAuthRoute(auth)).toEqual({ kind: "allow" })
    })
})
