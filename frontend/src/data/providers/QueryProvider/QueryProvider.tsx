import { type ReactNode } from "react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"

export function QueryProvider({ 
    client,
    children 
}: { client: QueryClient, children: ReactNode }) {    
    return (
        <QueryClientProvider client={client}>
            {children}
        </QueryClientProvider>
    )
}