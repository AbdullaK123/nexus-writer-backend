import { getVariantStyle } from "./utils";


export type StatusBadgeVariant = "ongoing" | "complete" | "hiatus" | "error" | "draft"

type StatusBadgeProps = {
    variant: StatusBadgeVariant
}


export function StatusBadge({ variant }: StatusBadgeProps) {
    const variantStyleAndText = getVariantStyle(variant)
    return (
        <span className={`status-badge ${variantStyleAndText.variant}`}>
            {variantStyleAndText.text}
        </span>
    )
}