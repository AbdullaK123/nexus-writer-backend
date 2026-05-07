import { type DefaultOptions } from "@tanstack/react-query"

/**
 * Default cache behaviour for the app.
 *
 * Tuning rationale:
 *   - This is an editor-style app: most data changes via the user's own
 *     mutations (which we invalidate explicitly), not via background
 *     server activity. Aggressive auto-refetch is noise.
 *   - `staleTime: 30s` means re-mounted components (route changes,
 *     panel toggles) hit the cache rather than the network.
 *   - `gcTime: 5m` keeps unmounted query data warm long enough to
 *     survive a navigation round-trip without losing context.
 *   - `refetchOnWindowFocus: false` because writers leave the tab
 *     in the background while drafting elsewhere; surprise refetches
 *     fight the editor's own state.
 *   - Mutations don't retry — every mutation is user-initiated and a
 *     silent retry can double-apply side effects.
 */
export const queryClientDefaults: DefaultOptions = {
    queries: {
        staleTime: 30 * 1000,
        gcTime: 5 * 60 * 1000,
        refetchOnWindowFocus: false,
        retry: 1,
    },
    mutations: {
        retry: 0,
    },
}