import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { api } from "../../infrastructure/api"
import type {
    AuthCredentials,
    RegistrationData,
    UserResponse,
    ApiMessage
} from "../../infrastructure/api/types"

export const authKeys = {
    all: ["auth"] as const,
    me: () => [...authKeys.all, "me"] as const
}

export function useCurrentUser() {
    return useQuery({
        queryKey: authKeys.me(),
        queryFn: ({ signal }) => api.auth.getCurrentUser({ signal }),
        staleTime: 5*60*1000,
        retry: false
    })
}

export function useLogin() {
    const qc = useQueryClient()
    return useMutation<UserResponse, Error, AuthCredentials>({
        mutationFn: (payload) => api.auth.login(payload),
        onSuccess: (user) => {
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useRegister() {
    const qc = useQueryClient()
    return useMutation<UserResponse, Error, RegistrationData>({
        mutationFn: (payload) => api.auth.register(payload),
        onSuccess: (user) => {
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useLogout() {
    const qc = useQueryClient()
    return useMutation<ApiMessage, Error, void>({
        mutationFn: () => api.auth.logout(),
        // Auth changes invalidate EVERYTHING — every cached query is
        // user-scoped on the backend.
        onSuccess: () => {
            qc.clear()
        },
    })
}
