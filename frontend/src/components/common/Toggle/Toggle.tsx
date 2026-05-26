import { type ReactNode } from "react"
import { Toggle as ArcToggle } from "@ark-ui/react/toggle"


type ToggleProps = {
    children: ReactNode
}

export function Toggle({ children }: ToggleProps) {
    return (
        <ArcToggle.Root>
            {children}
        </ArcToggle.Root>
    )
}