import { Some } from "oxide.ts";
import { Button, ErrorState, Nothing } from "../../../common";
import { CardLoadingSkeleton } from "../../../story/CardLoadingSkeleton";
import { CharacterAppearanceDensityChart, type CharacterAppearanceDensityChartProps } from "./CharacterAppearanceDensityChart/CharacterAppearanceDensityChart";
import { CharacterBarChart, type CharacterBarChartProps } from "./CharacterBarChart/CharacterBarChart";
import { CharacterCoOccurenceMatrix, type CharacterCoOccurenceMatrixProps } from "./CharacterCoOcurrenceMatrix/CharacterCoOcurrenceMatrix";
import { CharacterSuggestionCard, type CharacterSuggestionCardProps } from "./CharacterSuggestionCard/CharacterSuggestionCard";

export type CharacterDashboardProps = 
| { status: "idle" }
| { status: "empty" }
| { status: "loading"}
| { status: "error", onRetry: () => void}
| {
    status: "ready"
    suggestion: CharacterSuggestionCardProps
    castStatistics: CharacterBarChartProps
    coOccurenceStatistics: CharacterCoOccurenceMatrixProps
    density: CharacterAppearanceDensityChartProps
  }


export function CharacterDashboard(props: CharacterDashboardProps) {
    switch (props.status) {
        case "loading": {
            return (
                <div>
                    <div>
                        <CardLoadingSkeleton />
                    </div>
                    <div>
                        <div>
                            <CardLoadingSkeleton />
                        </div>
                        <div>
                            <CardLoadingSkeleton />
                            <CardLoadingSkeleton />
                        </div>
                    </div>
                </div>
            )
        }
        case "idle":
        case "empty": {
            return <Nothing />
        }
        case "error": {
            return (
                <div>
                    <ErrorState 
                        headline="Error"
                        title="Failed to fetch character dashboard"
                        description={
                            Some(
                                "Something went wrong. The server might be experiencing issues."
                            )
                        }
                        action={
                            Some(
                                <Button
                                    variant="primary"
                                    onClick={props.onRetry}
                                >
                                    Retry
                                </Button>
                            )
                        }
                    />
                </div>
            )
        }
        case "ready": {
            return (
                <div>
                    <div>
                        <CharacterSuggestionCard {...props.suggestion} />
                    </div>
                    <div>
                        <div>
                            <CharacterBarChart {...props.castStatistics} />
                        </div>
                        <div>
                            <CharacterCoOccurenceMatrix {...props.coOccurenceStatistics} />
                            <CharacterAppearanceDensityChart {...props.density} />
                        </div>
                    </div>
                </div>
            )
        }
    }
}