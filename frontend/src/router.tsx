import {
    createRouter,
    createRoute,
    Outlet,
    redirect,
    createRootRouteWithContext
} from "@tanstack/react-router"
import { DashboardPage } from "./components/story";
import { LoginPage } from "./components/auth";
import type { AuthContextValue } from "./data/providers/AuthProvider/AuthContext"
import { None } from "oxide.ts";
import { Background } from "./components/common/Background/Background";

interface RouterContext {
    auth: AuthContextValue
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
    component: () => (
        <>
            <Background />
            <div className="app-shell">
                <Outlet />
            </div>
        </>
    ),
})

const loginRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/login",
    validateSearch: (s: Record<string, unknown>) => ({
        redirect: typeof s.redirect === "string" ? s.redirect : undefined
    }),
    component: LoginPage
})

const appRoute = createRoute({
    getParentRoute: () => rootRoute,
    id: "app",
    beforeLoad: ({ context, location}) => {
        const { status, user } = context.auth 
        if (status === "loading") return 
        if (status === "authenticated" && user.isSome()) return 
        throw redirect({
            to: "/login",
            search: {redirect: location.href}
        })
    },
    component: () => <Outlet />
})

const dashboardRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/",
    component: DashboardPage
})

const routeTree = rootRoute.addChildren([
    loginRoute,
    appRoute.addChildren([dashboardRoute])
])

export const router = createRouter({
    routeTree,
    context: {
        auth: {
            user: None,
            status: "loading",
            error: None
        }
    }
})

declare module "@tanstack/react-router" {
    interface Register { router: typeof router }
}