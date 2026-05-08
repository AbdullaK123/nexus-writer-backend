import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { loadConfig } from './infrastructure/config'
import { createApi } from './infrastructure/api'
import { ApiProvider, AuthProvider, QueryProvider } from './data/providers'
import { match, fromNullable } from './shared/types'

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
                createRoot(rootEl).render(
                    <StrictMode>
                        <QueryProvider>
                            <ApiProvider api={api}>
                                <AuthProvider>
                                    <App />
                                </AuthProvider>
                            </ApiProvider>
                        </QueryProvider>
                    </StrictMode>,
                )
            },
        })
    },
})
