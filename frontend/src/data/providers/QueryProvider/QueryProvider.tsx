import { type ReactNode, useState } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { queryClientDefaults } from "./config"

export function QueryProvider({ children }: { children: ReactNode }) {
    const [client] = useState(() => new QueryClient({ defaultOptions: queryClientDefaults}))
    return (
        <QueryClientProvider client={client}>
            {children}
        </QueryClientProvider>
    )
}