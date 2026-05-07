import { createContext, useContext } from "react"
import type { UserResponse } from "../../../infrastructure/api/types"

export type AuthContextValue = {
    user: UserResponse | null
    isLoading: boolean
    isAuthenticated: boolean
}

export const AuthContext = createContext<AuthContextValue | null>(null)

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext)
    if (ctx === null) {
        throw new Error("useAuth must be used inside <AuthProvider>")
    }
    return ctx
}