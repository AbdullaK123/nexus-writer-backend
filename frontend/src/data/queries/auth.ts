import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type AuthCredentials,
    type RegistrationData,
    type UserResponse,
    type ApiMessage,
    requestOptions,
} from "../../infrastructure/api/types"
import { unwrapResultAsync } from "../../shared/types"

export const authKeys = {
    all: ["auth"] as const,
    me: () => [...authKeys.all, "me"] as const
}

export function useCurrentUser() {
    const api = useApi()
    return useQuery({
        queryKey: authKeys.me(),
        queryFn: ({ signal }) => unwrapResultAsync(api.auth.getCurrentUser(requestOptions({ signal }))),
        staleTime: 5*60*1000,
        retry: false
    })
}

export function useLogin() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<UserResponse, Error, AuthCredentials>({
        mutationFn: (payload) => unwrapResultAsync(api.auth.login(payload)),
        onSuccess: (user) => {
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useRegister() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<UserResponse, Error, RegistrationData>({
        mutationFn: (payload) => unwrapResultAsync(api.auth.register(payload)),
        onSuccess: (user) => {
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useLogout() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<ApiMessage, Error, void>({
        mutationFn: () => unwrapResultAsync(api.auth.logout()),
        // Auth changes invalidate EVERYTHING — every cached query is
        // user-scoped on the backend.
        onSuccess: () => {
            qc.clear()
        },
    })
}
