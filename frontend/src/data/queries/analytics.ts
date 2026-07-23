import { useQuery } from "@tanstack/react-query";
import { type CharacterDashboardResponse, type PlotDashboardResponse, type StructureDashboardResponse, type WorldDashboardResponse } from "../../infrastructure/api/types/analytics";
import { useApi } from "../providers";
import { unwrapResultAsync, type ApiError } from "../../shared/types";
import { requestOptions } from "../../infrastructure/api/types";
import { toAsyncState } from "../../infrastructure/api/utils";



export const dashboardKeys = {
    all: ["dashboard"] as const,
    character: (storyId: string) => [...dashboardKeys.all, storyId, "dashboard", "character"] as const,
    plot: (storyId: string) => [...dashboardKeys.all, storyId, "dashboard", "plot"] as const,
    structure: (storyId: string) => [...dashboardKeys.all, storyId, "dashboard", "structure"] as const,
    world: (storyId: string) => [...dashboardKeys.all, storyId, "dashboard", "world"] as const
}


export function useCharacterDashboard(storyId: string) {
    const api = useApi()
    const result = useQuery<CharacterDashboardResponse, ApiError>({
        queryKey: dashboardKeys.character(storyId),
        queryFn: ({ signal }) => unwrapResultAsync<CharacterDashboardResponse, ApiError>(api.story.getCharacterDashboard(storyId, requestOptions({ signal }))),
    })
    return [toAsyncState<CharacterDashboardResponse>(result), result.refetch] as const
}

export function usePlotDashboard(storyId: string) {
    const api = useApi()
    const result = useQuery<PlotDashboardResponse, ApiError>({
        queryKey: dashboardKeys.character(storyId),
        queryFn: ({ signal }) => unwrapResultAsync<PlotDashboardResponse, ApiError>(api.story.getPlotDashboard(storyId, requestOptions({ signal }))),
    })
    return [toAsyncState<PlotDashboardResponse>(result), result.refetch] as const
}

export function useStructureDashboard(storyId: string) {
    const api = useApi()
    const result = useQuery<StructureDashboardResponse, ApiError>({
        queryKey: dashboardKeys.character(storyId),
        queryFn: ({ signal }) => unwrapResultAsync<StructureDashboardResponse, ApiError>(api.story.getStuctureDashboard(storyId, requestOptions({ signal }))),
    })
    return [toAsyncState<StructureDashboardResponse>(result), result.refetch] as const
}

export function useWorldDashboard(storyId: string) {
    const api = useApi()
    const result = useQuery<WorldDashboardResponse, ApiError>({
        queryKey: dashboardKeys.character(storyId),
        queryFn: ({ signal }) => unwrapResultAsync<WorldDashboardResponse, ApiError>(api.story.getWorldDashboard(storyId, requestOptions({ signal }))),
    })
    return [toAsyncState<WorldDashboardResponse>(result), result.refetch] as const
}