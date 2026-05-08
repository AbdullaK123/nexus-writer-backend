import { createContext } from "react"
import type { AppApi } from "../../../infrastructure/api"

/**
 * The api singleton, created by `main.tsx` after config loads, lives
 * here. Components access it via `useApi()`. Tests can mount the
 * provider with a fake `AppApi` to exercise hooks without HTTP.
 */
export const ApiContext = createContext<AppApi | null>(null)
