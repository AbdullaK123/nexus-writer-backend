import type { StoryStatus } from "../../../../infrastructure/api/types";
import type { StatusBadgeVariant } from "../../../common";

export const toStatusBadgeVariant = (status: StoryStatus): StatusBadgeVariant => {
    switch (status) {
        case "Complete": return "complete"
        case "On Hiatus": return "hiatus"
        case "Ongoing": return "ongoing"
        default: return "ongoing"
    }
}