import { createContext, useContext } from "react"
import type { UserResponse } from "../../../infrastructure/api/types"
import {
    Err,
    Ok,
    fromNullable,
    type Option,
    type Result,
} from "../../../shared/types"

export type AuthStatus =
    | "loading"
    | "authenticated"
    | "unauthenticated"
    | "error"

export type AuthContextValue = {
    user: Option<UserResponse>
    status: Option<AuthStatus>
    error: Option<Error>
}

export class AuthContextMissingError extends Error {
    readonly _tag = "AuthContextMissingError" as const
    constructor() {
        super("useAuth must be used inside <AuthProvider>")
        this.name = "AuthContextMissingError"
    }
}

export const AuthContext = createContext<AuthContextValue | null>(null)

/**
 * Returns the auth context as a Result. `Err` is only produced when the hook
 * is used outside of `<AuthProvider>` — a programmer error, not a runtime
 * condition. Callers that are statically guaranteed to be under the provider
 * may use `useAuthOrThrow()` instead.
 */
export function useAuth(): Result<AuthContextValue, AuthContextMissingError> {
    const ctx = fromNullable(useContext(AuthContext))
    return ctx.isNone()
        ? Err(new AuthContextMissingError())
        : Ok(ctx.unwrap())
}

/**
 * Boundary helper for callers that are statically guaranteed to live under
 * `<AuthProvider>`. Throws on misuse — this is the one place the throw is
 * allowed, mirroring `unwrapResultAsync` in the React Query layer.
 */
export function useAuthOrThrow(): AuthContextValue {
    return useAuth().unwrap()
}