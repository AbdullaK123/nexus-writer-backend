import { useParams } from "@tanstack/react-router";
import { useCharacterDashboard } from "../../../../data/queries/analytics";
import type { CharacterDashboardProps } from "./CharacterDashboard";



export function useCharacterDashboardPageProps(): CharacterDashboardProps {

    const params = useParams({ from: "/app/stories/$storyId/analytics"})

    const [characterDashboardState, refetchCharacterDashboardState] = useCharacterDashboard(params.storyId)

    switch (characterDashboardState.status) {
        case "loading":
        case "empty":
        case "idle": {
            return { status: characterDashboardState.status}
        }
        case "error": {
            return {
                status: "error",
                onRetry: refetchCharacterDashboardState
            }
        }
        case "success": {

            const data = characterDashboardState.data.unwrap().unwrap()

            return {
                status: "ready",
                suggestion: {
                    ...data.suggestion.suggestion,
                    onAskNexus: () => {}
                },
                castStatistics: {
                    data: data.castStatistics.statistics
                },
                coOccurenceStatistics: {
                    data: data.coOccurenceStatistics.statistics
                },
                density: {
                    data: data.characterStatistics.statistics
                }
            }
        }
    }
}