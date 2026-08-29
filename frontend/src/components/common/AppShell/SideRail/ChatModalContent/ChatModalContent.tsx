import { None, Some, Option } from "oxide.ts";
import type { AsyncState, StoryNavigationResponse } from "../../../../../infrastructure/api/types";
import type { ApiError } from "../../../../../shared/types";
import { LoadingSkeleton } from "../../../LoadingSkeleton";
import { Nothing } from "../../../Nothing";
import { Select, type Option as SelectOption } from "../../../Select";

export interface ChatModalContentProps {
    state: AsyncState<StoryNavigationResponse, ApiError>,
    onRetry: () => void
    onChange: (storyId: string) => void
}

export const ChatModalContent = ({
    state,
    onChange
}: ChatModalContentProps): React.ReactNode => {
    switch (state.status) {
        case "empty":
        case "idle":
            return <Nothing />
        case "loading":
            return (
                <div className="flex-col">
                    <h2>What story do you want to chat with?</h2>
                    <LoadingSkeleton className={None} />
                </div>
            )
        case "success": {
            const links = state.data.unwrap().unwrap().links;
            const options = links.map((link) => ({
                label: link.title,
                value: Some(link.storyId)
            })) as SelectOption<Option<string>>[];

            return (
                <div className="flex-col">
                    <h2>What story do you want to chat with?</h2>
                    <Select<Option<string>>
                        label=""
                        options={options}
                        defaultChecked
                        defaultValue="Choose a story..."
                        onChange={(value) => {
                            if (value.isSome()) onChange(value.unwrap())
                        }}
                    />
                </div>
            )
        }
    }
}
