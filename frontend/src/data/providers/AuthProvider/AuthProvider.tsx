import { type ReactNode } from "react"
import { useCurrentUser } from "../../queries"
import {
    None,
    Some,
} from "../../../shared/types"
import {
    AuthContext,
    type AuthContextValue,
} from "./AuthContext"

export function AuthProvider({ children }: { children: ReactNode }) {
    const authState = useCurrentUser()

    let ctx = {} as AuthContextValue

    switch (authState.status) {
        case "empty":
            ctx = {
                user: None,
                status: Some("unauthenticated"),
                error: None
            }
            break;
        case "error":
            ctx = {
                user: None,
                status: Some("error"),
                error: Some(authState.data.unwrap().unwrapErr())
            }
            break;
        case "idle":
        case "loading":
            ctx = {
                user: None,
                status: Some("loading"),
                error: None
            }
            break;
        case "success":
            ctx = {
                user: Some(authState.data.unwrap().unwrap()),
                status: Some("authenticated"),
                error: None
            }
            break;

    }

    return <AuthContext.Provider value={ctx}>{children}</AuthContext.Provider>
}

