import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AppRouter} from "./AppRouter.tsx"
import { loadConfig } from './infrastructure/config'
import { createApi } from './infrastructure/api'
import { ApiProvider, AuthProvider, QueryProvider } from './data/providers'
import { match, fromNullable, ApiError } from './shared/types'
import { QueryCache, QueryClient } from '@tanstack/react-query';
import { queryClientDefaults } from './data/providers/QueryProvider/config.ts';
import { Toast } from './components/common/Toast/Toast.tsx';
import { router } from "./router"

// ─── Composition root ───────────────────────────────────────
//
// The ONLY place in the app that bridges from raw nullable / throwing
// APIs (`document.getElementById`, env config) into the Option/Result
// world the rest of the code lives in. Every failure mode has an
// explicit branch — no `!`, no `throw` outside of `match`.

const configResult = loadConfig()

const rootOpt = fromNullable(document.getElementById('root'))

match(rootOpt, {
    None: () => {
        // Index.html is missing <div id="root">. Render a minimal
        // failure surface into <body> so the user sees something.
        document.body.innerHTML =
            '<pre style="padding:1rem;color:#b00">Boot failure: missing #root element in index.html</pre>'
    },
    Some: (rootEl) => {
        match(configResult, {
            Err: (err) => {
                createRoot(rootEl).render(
                    <StrictMode>
                        <pre
                            style={{
                                padding: '1rem',
                                color: '#b00',
                                whiteSpace: 'pre-wrap',
                            }}
                        >
                            {err.message}
                        </pre>
                    </StrictMode>,
                )
            },
            Ok: (config) => {
                const api = createApi(config)
                const queryClient = new QueryClient({ 
                    defaultOptions: queryClientDefaults,
                    queryCache: new QueryCache({
                        onError: (error) => {

                            const from = router.state.location.pathname

                            if (error instanceof ApiError) {
                                switch (error.status) {
                                    case 401: 
                                        router.navigate({ to: "/login", search: { redirect: from }})
                                        break
                                    case 404: 
                                        router.navigate({ to: "/404", search: { redirect: from }})
                                        break
                                    default: 
                                        router.navigate({ to: "/error", search: { redirect: from }})
                                }
                            } else {
                                router.navigate({ to: "/error", search: { redirect: from }})
                            }

                        }
                    })
                 })
                createRoot(rootEl).render(
                    <StrictMode>
                        <QueryProvider client={queryClient}>
                            <ApiProvider api={api}>
                                <AuthProvider>
                                    <Toast>
                                        <AppRouter />
                                    </Toast>
                                </AuthProvider>
                            </ApiProvider>
                        </QueryProvider>
                    </StrictMode>,
                )
            },
        })
    },
})
