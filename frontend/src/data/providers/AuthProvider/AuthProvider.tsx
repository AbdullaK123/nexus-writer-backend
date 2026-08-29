import { type ReactNode } from "react"
import { useCurrentUser } from "../../queries"
import {
    AuthContext,
    type AuthContextValue,
} from "./AuthContext"
import { ApiError } from "../../../shared/types"

export function AuthProvider({ children }: { children: ReactNode }) {
    const authState = useCurrentUser()

    let ctx = {} as AuthContextValue

    switch (authState.status) {
        case "idle":
        case "loading":
            ctx = { status: "loading" }
            break
        case "empty":
            ctx = { status: "unauthenticated" }
            break
        case "error": {
            const error = authState.data.unwrap().unwrapErr()
            ctx =
                error instanceof ApiError && error.status === 401
                    ? { status: "unauthenticated" }
                    : { status: "error", error }
            break
        }
        case "success":
            ctx = { status: "authenticated", user: authState.data.unwrap().unwrap() }
            break
    }

    return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>
}
