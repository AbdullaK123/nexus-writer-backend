import { type ReactNode } from "react"
import type { AppApi } from "../../../infrastructure/api"
import { ApiContext } from "./ApiContext"

interface ApiProviderProps {
    api: AppApi
    children: ReactNode
}

export function ApiProvider({ api, children }: ApiProviderProps) {
    return <ApiContext.Provider value={api}>{children}</ApiContext.Provider>
}
