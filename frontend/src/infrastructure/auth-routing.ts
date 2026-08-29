import type { AuthContextValue } from "../data/providers/AuthProvider/AuthContext"

export type AppAuthDecision =
    | { kind: "allow" }
    | { kind: "redirect-login"; redirect: string }

export type LoginAuthDecision =
    | { kind: "allow" }
    | { kind: "redirect-home" }

export function decideAppAuthRoute(
    auth: AuthContextValue,
    locationHref: string,
): AppAuthDecision {
    if (auth.status === "loading" || auth.status === "authenticated") {
        return { kind: "allow" }
    }

    return { kind: "redirect-login", redirect: locationHref }
}

export function decideLoginAuthRoute(auth: AuthContextValue): LoginAuthDecision {
    return auth.status === "authenticated"
        ? { kind: "redirect-home" }
        : { kind: "allow" }
}
