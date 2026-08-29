import { type ReactNode } from "react"
import { useCurrentUser } from "../../queries"
import {
    AuthContext,
    type AuthContextValue,
} from "./AuthContext"

export function AuthProvider({ children }: { children: ReactNode }) {
    const authState = useCurrentUser()

    let ctx: AuthContextValue

    switch (authState.status) {
        case "loading":
            ctx = { status: "loading" }
            break
        case "unauthenticated":
            ctx = { status: "unauthenticated" }
            break
        case "error":
            ctx = { status: "error", error: authState.error }
            break
        case "authenticated":
            ctx = { status: "authenticated", user: authState.user }
            break
    }

    return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>
}
