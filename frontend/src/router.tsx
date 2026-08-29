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
import { Background } from "./components/common/Background/Background";
import { SignupPage } from "./components/auth/SignupPage";
import { AppShell } from "./components";
import { StoryDetailPage } from "./components/story/StoryDetailPage/StoryDetailPage";
import { ChapterEditorPage } from "./components/chapter/ChapterEditorPage";
import { StoryChatPage } from "./components/chat";
import { NewStoryChatPage } from "./components/chat/StoryChatPage/NewStoryChatPage";
import { z } from "zod";
import { SettingsPage } from "./components/settings";
import { ErrorPage } from "./components/common/ErrorPage";
import { NotFoundPage } from "./components/common/NotFoundPage";
import { decideAppAuthRoute, decideLoginAuthRoute } from "./infrastructure/auth-routing";

export interface RouterContext {
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
    beforeLoad: ({ context }) => {
        const decision = decideLoginAuthRoute(context.auth)
        if (decision.kind === "redirect-home") {
            throw redirect({ to: "/" })
        }
    },
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

export const errorRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/error",
    validateSearch: (s: Record<string, unknown>) => ({
        redirect: typeof s.redirect === "string" ? s.redirect : undefined
    }),
    component: ErrorPage
})

export const notFoundRoute = createRoute({
    getParentRoute: () => rootRoute,
    path: "/404",
    validateSearch: (s: Record<string, unknown>) => ({
        redirect: typeof s.redirect === "string" ? s.redirect : undefined
    }),
    component: NotFoundPage
})

const appRoute = createRoute({
    getParentRoute: () => rootRoute,
    id: "app",
    beforeLoad: ({ context, location}) => {
        const decision = decideAppAuthRoute(context.auth, location.href)
        if (decision.kind === "redirect-login") {
            throw redirect({
                to: "/login",
                search: { redirect: decision.redirect },
            })
        }
    },
    component: () => {
        return (
            <AppShell>
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
    getParentRoute: () => appRoute,
    path: "/stories/$storyId/$chapterId",
    component: ChapterEditorPage
})

const storyChatRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/stories/$storyId/chat/$threadId",
    component: StoryChatPage,
    validateSearch: z.object({
        prompt: z.string().optional()
    })
})

const newStoryChatRoute = createRoute({
    getParentRoute: () => appRoute,
    path: "/stories/$storyId/chat/new",
    component: NewStoryChatPage
})

const settingsPage = createRoute({
    getParentRoute: () => appRoute,
    path: "/settings",
    component: SettingsPage
})

export const routeTree = rootRoute.addChildren([
    loginRoute,
    signupRoute,
    errorRoute,
    notFoundRoute,
    appRoute.addChildren([
        dashboardRoute,
        storyDetailRoute,
        chapterEditorRoute,
        storyChatRoute,
        newStoryChatRoute,
        settingsPage
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
