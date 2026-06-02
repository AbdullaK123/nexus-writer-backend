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
import { SignupPage } from "./components/auth/SignupPage";
import { AppShell, KitchenSink } from "./components";

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

const signupRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/signup",
    validateSearch: (s: Record<string, unknown>) => ({
        redirect: typeof s.redict === "string" ? s.redirect : undefined
    }),
    component: SignupPage
})

const devRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/dev",
    component: KitchenSink
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
    component: () => (
        <AppShell
            sideRail={{
                onClickHome: ()=>{},
                onClickChat: ()=>{},
                onClickStat: ()=>{},
                onClickSet: ()=>{},
                onClickEdit: ()=>{}
            }}
        >
            <Outlet />
        </AppShell>
    )
})

const dashboardRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/",
    component: DashboardPage
})

const routeTree = rootRoute.addChildren([
    loginRoute,
    signupRoute,
    devRoute,
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