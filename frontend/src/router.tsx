import {
    createRouter,
    createRoute,
    Outlet,
    redirect,
    createRootRouteWithContext,
    useNavigate,
} from "@tanstack/react-router"
import { DashboardPage } from "./components/story";
import { LoginPage } from "./components/auth";
import type { AuthContextValue } from "./data/providers/AuthProvider/AuthContext"
import { Background } from "./components/common/Background/Background";
import { SignupPage } from "./components/auth/SignupPage";
import { AppShell, KitchenSink } from "./components";
import { StoryDetailPage } from "./components/story/StoryDetailPage/StoryDetailPage";
import { ChapterEditorPage } from "./components/chapter/ChapterEditorPage";

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
        redirect: typeof s.redirect === "string" ? s.redirect : undefined
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
        const ctx = context.auth 
        switch (ctx.status) {
            case "loading": return 
            case "authenticated": return
            default:
                throw redirect({
                    to: "/login",
                    search: {redirect: location.href}
                })
        } 
    },
    component: () => {
        // eslint-disable-next-line react-hooks/rules-of-hooks
        const navigate = useNavigate() 

        return (
            <AppShell
                sideRail={{
                    onClickHome: () => navigate({ to: "/" }),
                    onClickChat: () => {},
                    onClickStat: () => {},
                    onClickSet: () => {},
                    onClickEdit: () => {}
                }}
            >
                <Outlet />
            </AppShell>
        )
    }
})

const dashboardRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/",
    component: DashboardPage
})

const storyDetailRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/stories/$storyId",
    component: StoryDetailPage
})

const chapterEditorRoute = createRoute({
    getParentRoute: () => storyDetailRoute,
    path: "/$chapterId",
    component: ChapterEditorPage
})

const routeTree = rootRoute.addChildren([
    loginRoute,
    signupRoute,
    devRoute,
    appRoute.addChildren([
        dashboardRoute, 
        storyDetailRoute,
        chapterEditorRoute
    ])
])

export const router = createRouter({
    routeTree,
    context: {
        auth: {status: "unauthenticated"}
    }
})

declare module "@tanstack/react-router" {
    interface Register { router: typeof router }
}