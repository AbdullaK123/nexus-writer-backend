import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useApi } from "../providers/ApiProvider"
import {
    type AuthCredentials,
    type RegistrationData,
    type UserResponse,
    type ApiMessage,
    requestOptions,
    type DashboardResponse,
    type UserNavigationResponse,
    type StoryNavigationResponse,
    type SettingsPayload,
} from "../../infrastructure/api/types"
import { ApiError, unwrapResultAsync } from "../../shared/types"
import { toAsyncState } from "../../infrastructure/api/utils";

export const authKeys = {
    all: ["auth"] as const,
    me: () => [...authKeys.all, "me"] as const,
    dashboard: () => [...authKeys.all, "me", "dashboard"],
    editorLinks: () => [...authKeys.all, "me", "links", "editor"],
    chatLinks: () => [...authKeys.all, "me", "links", "chat"]
}

export type CurrentUserState =
    | { status: "loading" }
    | { status: "unauthenticated" }
    | { status: "authenticated"; user: UserResponse }
    | { status: "error"; error: ApiError }

export function useCurrentUser(): CurrentUserState {
    const api = useApi()
    const query = useQuery<UserResponse, ApiError>({
        queryKey: authKeys.me(),
        queryFn: ({ signal }) => unwrapResultAsync(api.auth.getCurrentUser(requestOptions({ signal }))),
        staleTime: 5*60*1000,
        retry: false
    })

    if (query.isPending) {
        return { status: "loading" }
    }

    if (query.isError) {
        return query.error.status === 401
            ? { status: "unauthenticated" }
            : { status: "error", error: query.error }
    }

    return { status: "authenticated", user: query.data }
}

export function useDashboard() {
    const api = useApi()
    const result = useQuery<DashboardResponse, ApiError>({
        queryKey: authKeys.dashboard(),
        queryFn: ({ signal }) => unwrapResultAsync(api.auth.getDashboard(requestOptions({ signal }))),
        staleTime: 5*60*100
    })
    return toAsyncState<DashboardResponse>(result)
}

export function useUpdateSettings() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<UserResponse, ApiError, SettingsPayload> ({
        mutationFn: (payload) => unwrapResultAsync(api.auth.updateSettings(payload)),
        onSuccess: (user) => {
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useEditorLinks() {
    const api = useApi()
    const result = useQuery<UserNavigationResponse, ApiError>({
        queryKey: authKeys.editorLinks(),
        queryFn: ({ signal }) => unwrapResultAsync(api.auth.getEditorLinks(requestOptions({ signal }))),
        staleTime: 5*60*100
    })
    return [toAsyncState<UserNavigationResponse>(result), result.refetch] as const
}

export function useChatLinks() {
    const api = useApi()
    const result = useQuery<StoryNavigationResponse, ApiError>({
        queryKey: authKeys.chatLinks(),
        queryFn: ({ signal }) => unwrapResultAsync(api.auth.getChatLinks(requestOptions({ signal }))),
        staleTime: 5*60*100
    })
    return [toAsyncState<StoryNavigationResponse>(result), result.refetch] as const
}

export function useLogin() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<UserResponse, ApiError, AuthCredentials>({
        mutationFn: (payload) => unwrapResultAsync(api.auth.login(payload)),
        onSuccess: (user) => {
            qc.clear()
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useRegister() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<UserResponse, ApiError, RegistrationData>({
        mutationFn: (payload) => unwrapResultAsync(api.auth.register(payload)),
        onSuccess: (user) => {
            qc.clear()
            qc.setQueryData(authKeys.me(), user)
        }
    })
}

export function useLogout() {
    const api = useApi()
    const qc = useQueryClient()
    return useMutation<ApiMessage, ApiError, void>({
        mutationFn: () => unwrapResultAsync(api.auth.logout()),
        // Auth changes invalidate EVERYTHING — every cached query is
        // user-scoped on the backend.
        onSuccess: () => {
            qc.clear()
        },
    })
}
