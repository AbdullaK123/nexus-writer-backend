

type StatusBadgeVariant = "ongoing" | "complete" | "hiatus" | "error" | "draft"

type StatusBadgeProps = {
    variant: StatusBadgeVariant
}

const getVariantStyle = (variant: StatusBadgeVariant)  => {
    switch (variant) {
        case "complete": return {variant: "status-badge--complete", text: "COMPLETE"}
        case "ongoing": return {variant: "status-badge--ongoing", text: "ONGOING"}
        case "hiatus": return {variant: "status-badge--hiatus", text: "HIATUS"}
        case "error": return {variant: "status-badge--error", text: "ERROR"}
        case "draft": return {variant:"status-badge--draft", text: "DRAFT"}
    }
}


export function StatusBadge({ variant }: StatusBadgeProps) {
    const variantStyleAndText = getVariantStyle(variant)
    return (
        <span className={`status-badge ${variantStyleAndText.variant}`}>
            {variantStyleAndText.text}
        </span>
    )
}