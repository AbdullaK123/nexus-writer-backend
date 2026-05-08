import { useContext } from "react"
import { ApiContext } from "./ApiContext"
import { fromNullable, type Option } from "../../../shared/types"
import type { AppApi } from "../../../infrastructure/api"

/**
 * Read the api off context as `Option<AppApi>`. Returns `None` when
 * the hook is called outside an `ApiProvider` — callers decide how to
 * handle the absence (typically `.expect(...)` at the query-layer
 * boundary, where missing api means a programmer error).
 */
export function useApiOption(): Option<AppApi> {
    return fromNullable(useContext(ApiContext))
}

/**
 * Boundary helper for query hooks. Throws iff called outside an
 * `ApiProvider`, which is a programmer error (the provider is mounted
 * unconditionally at the composition root in `main.tsx`).
 *
 * Mirrors the React Query bridge `unwrapResultAsync`: explicit named
 * adapter, used only at the layer that has no other recourse.
 */
export function useApi(): AppApi {
    return useApiOption().expect(
        "useApi() called outside an <ApiProvider> tree",
    )
}
