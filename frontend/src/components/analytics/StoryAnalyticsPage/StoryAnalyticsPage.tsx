import { Outlet } from "@tanstack/react-router";
import { AnalyticsHeader, type AnalyticsHeaderProps } from "./AnalyticsHeader/AnalyticsHeader";


export type StoryAnalyticsPageProps = 
{
    header: AnalyticsHeaderProps
}

export function StoryAnalyticsPage() {
    return (
        <div>
            <AnalyticsHeader  />
            <Outlet />
        </div>
    )
}