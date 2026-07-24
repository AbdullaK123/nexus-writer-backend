
import { useParams } from "@tanstack/react-router";
import { useStoryStats } from "../../../data/queries";
import type { StoryAnalyticsPageProps } from "./StoryAnalyticsPage";
import { useState } from "react";




export function useStoryAnalyticsPage(): StoryAnalyticsPageProps {

    const params = useParams({ from: "/app/stories/$storyId/analytics"})

    const [selectedLense, setSelectedLense] = useState<"character" | "plot" | "structure" | "world">("character")

    const [storyStatsState, refetchStats] = useStoryStats(params.storyId)

    switch (storyStatsState.status) {
        case "empty": 
        case "idle": {
            return { 
                header: {
                    status: storyStatsState.status
                }
            }
        }
        case "error": {
            return {
                header: {
                    status: "error",
                    onRetry: refetchStats
                }
            }
        }
        case "loading": {
            return {
                header: {
                    status: "loading"
                }
            }
        }
        case "success": {
            
            const data = storyStatsState.data.unwrap().unwrap()

            return {
                header: {
                    status: "ready",
                    storyTitle: data.storyTitle,
                    selectedLense: selectedLense,
                    onClickCharacter: () => setSelectedLense("character"),
                    onClickPlot: () => setSelectedLense("plot"),
                    onClickStructure: () => setSelectedLense("structure"),
                    onClickWorld: () => setSelectedLense("world")
                }
            }
        }
    }    


}