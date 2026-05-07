import { type ReactNode } from "react"
import type { UserResponse } from "../../../infrastructure/api/types";
import { useCurrentUser } from "../../queries";
import { AuthContext } from "./AuthContext";

type AuthContextValue = {
    user: UserResponse | null 
    isLoading: boolean
    isAuthenticated: boolean
}

export function AuthProvider({ children }: { children: ReactNode }) {
    const {data, isPending} = useCurrentUser()

    const value: AuthContextValue = {
        user: data ?? null,
        isLoading: isPending,
        isAuthenticated: Boolean(data)
    }

    return (
        <AuthContext.Provider value={value}>
            {children}
        </AuthContext.Provider>
    )
}



