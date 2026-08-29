import { ApiError } from "../shared/types"

export interface QueryErrorNavigation {
    to: "/login" | "/404" | "/error"
    search: { redirect: string }
}

export type NavigateOnQueryError = (navigation: QueryErrorNavigation) => unknown

export function routeQueryError(
    error: unknown,
    queryKey: readonly unknown[],
    from: string,
    navigate: NavigateOnQueryError,
): void {
    const isAuthProbe =
        queryKey.length === 2 &&
        queryKey[0] === "auth" &&
        queryKey[1] === "me"

    if (!(error instanceof ApiError)) {
        navigate({ to: "/error", search: { redirect: from } })
        return
    }

    if (error.status === 401) {
        if (isAuthProbe) return
        navigate({ to: "/login", search: { redirect: from } })
        return
    }

    if (error.status === 404) {
        navigate({ to: "/404", search: { redirect: from } })
        return
    }

    // Aborted React Query requests are expected during navigation/unmount.
    if (error.status === 0 && error.message === "Request was cancelled") {
        return
    }

    navigate({ to: "/error", search: { redirect: from } })
}
