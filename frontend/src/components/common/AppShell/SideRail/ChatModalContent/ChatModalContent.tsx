import { None, Some, Option } from "oxide.ts";
import type { AsyncState, StoryNavigationResponse } from "../../../../../infrastructure/api/types";
import type { ApiError } from "../../../../../shared/types";
import { LoadingSkeleton } from "../../../LoadingSkeleton";
import { Nothing } from "../../../Nothing";
import { ErrorState } from "../../../ErrorState";
import { Button } from "../../../Button";
import { Select, type Option as SelectOption } from "../../../Select";

export interface ChatModalContentProps {
    state: AsyncState<StoryNavigationResponse, ApiError>,
    onRetry: () => void
    onChange: (storyId: string) => void
}

export const ChatModalContent = ({
    state,
    onRetry,
    onChange
}: ChatModalContentProps): React.ReactNode => {
    switch (state.status) {
        case "empty":
        case "idle": {
            return <Nothing />
        }
        case "loading": {
            return (
                <div className="flex-col">
                    <h2>What story do you want to chat with?</h2>
                    <LoadingSkeleton className={None} />
                </div>
            )
        }
        case "error": {
            return (
                <ErrorState 
                    headline="Error"
                    title="Failed to fetch your links"
                    description={Some(
                        "Something went wrong. The server might be experiencing issues."
                    )}
                    action={Some(
                        <Button variant="primary" onClick={onRetry}>
                            Retry
                        </Button>
                    )}
                />
            )
        }
        case "success": {
            const links = state.data.unwrap().unwrap().links;

            const options = links.map((link) => ({
                label: link.title,
                value: Some(link.storyId)
            })) as SelectOption<Option<string>>[];

            return (
                <div className="flex-col">
                    <h2>What story do you want to chat with?</h2>
                    <Select
                        <Option<string>>
                        label=""
                        options={options}
                        defaultChecked
                        defaultValue={"Choose a story..."}
                        onChange={(value) => {
                            if (value.isSome()) {
                                const storyId = value.unwrap()
                                onChange(storyId)
                            }
                        }}
                    />
                </div>
            )
        }
    }
}