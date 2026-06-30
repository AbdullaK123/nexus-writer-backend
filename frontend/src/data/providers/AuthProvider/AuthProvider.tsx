import { type ReactNode } from "react"
import { useCurrentUser } from "../../queries"
import {
    AuthContext,
    type AuthContextValue,
} from "./AuthContext"

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
        case "error":
            ctx = { status: "error", error: authState.data.unwrap().unwrapErr() }
            break
        case "success":
            ctx = { status: "authenticated", user: authState.data.unwrap().unwrap() }
            break
    }

    return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>
}

