import { createContext, useContext } from "react"
import type { SettingsPayload, UserResponse, UserSettings } from "../../../infrastructure/api/types"
import { Option, Some, None} from "oxide.ts"
import {
    Err,
    Ok,
    fromNullable,
    type Result,
} from "../../../shared/types"
import { useUpdateSettings } from "../../queries";
import { useToast } from "../../../components";

export type AuthStatus =
    | "loading"
    | "authenticated"
    | "unauthenticated"
    | "error"

export type AuthContextValue =
    | { status: "loading" }
    | { status: "unauthenticated" }
    | { status: "error"; error: Error }
    | { status: "authenticated"; user: UserResponse }


export type SettingsContextValue = 
{
    settings: Option<UserSettings>,
    updateSettings: (payload: SettingsPayload) => void
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

export function useSettings(): SettingsContextValue {
    const auth = useAuthOrThrow()

    const {
        mutate: updateSettings,
    } = useUpdateSettings()

    const { error, success } = useToast()

    const settings =
        auth.status === "authenticated"
            ? Some(auth.user.settings)
            : None

    return {
        settings,

        updateSettings: (payload) =>
            updateSettings(payload, {
                onSuccess: () => {
                    success(
                        "Successfully updated settings",
                        "",
                    )
                },
                onError: () => {
                    error(
                        "Failed to update settings",
                        "Something went wrong. The server might be experiencing issues.",
                    )
                },
            }),
    }
}