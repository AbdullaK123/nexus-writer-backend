import { type ReactNode } from "react"
import { useCurrentUser } from "../../queries"
import {
    fromNullable,
    None,
    Some,
    type Option,
} from "../../../shared/types"
import {
    AuthContext,
    type AuthContextValue,
    type AuthStatus,
} from "./AuthContext"

export function AuthProvider({ children }: { children: ReactNode }) {
    const { data, isPending, isError, error } = useCurrentUser()

    const user = fromNullable(data)

    const status: AuthStatus = isPending
        ? "loading"
        : isError
        ? "error"
        : user.isSome()
        ? "authenticated"
        : "unauthenticated"

    const errorOpt: Option<Error> =
        isError && error instanceof Error ? Some(error) : None

    const value: AuthContextValue = {
        user,
        status,
        error: errorOpt,
    }

    return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

