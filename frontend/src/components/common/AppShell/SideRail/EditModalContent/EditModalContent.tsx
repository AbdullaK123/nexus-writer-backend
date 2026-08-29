import { None, Some, Option } from "oxide.ts";
import type { AsyncState, UserNavigationResponse } from "../../../../../infrastructure/api/types";
import type { ApiError } from "../../../../../shared/types";
import { LoadingSkeleton } from "../../../LoadingSkeleton";
import { Nothing } from "../../../Nothing";
import { Select, type Option as SelectOption } from "../../../Select";
import styles from "./EditModalContent.module.css"

export interface EditModalContentProps {
    state: AsyncState<UserNavigationResponse, ApiError>;
    onRetry: () => void;
    onChange: (args: { chapterId: string; storyId: string }) => void;
}

export const EditModalContent = ({
    state,
    onChange
}: EditModalContentProps): React.ReactNode => {
    switch (state.status) {
        case "empty":
        case "idle":
            return <Nothing />
        case "loading":
            return (
                <div className="flex-col">
                    <h2>What do you want to edit?</h2>
                    <LoadingSkeleton className={None} />
                </div>
            )
        case "success": {
            const links = state.data.unwrap().unwrap().links;
            const options = links.map((link) => ({
                label: link.label,
                value: Some({ chapterId: link.chapterId, storyId: link.storyId })
            })) as SelectOption<Option<{ chapterId: string; storyId: string }>>[];

            options.push({ label: "Choose a chapter", value: None })

            return (
                <div className="flex-col">
                    <h2>What do you want to edit?</h2>
                    <Select<Option<{ chapterId: string; storyId: string }>>
                        label=""
                        options={options}
                        defaultChecked
                        defaultValue="Choose a chapter..."
                        className={styles['select']}
                        onChange={(params) => {
                            if (params.isSome()) {
                                const routeParams = params.unwrap()
                                onChange({
                                    chapterId: routeParams.chapterId,
                                    storyId: routeParams.storyId
                                })
                            }
                        }}
                    />
                </div>
            )
        }
    }
}
