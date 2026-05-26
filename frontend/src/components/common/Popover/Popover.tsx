import { Popover as ArcPopover } from "@ark-ui/react/popover"
import { Portal } from "@ark-ui/react/portal"
import { type ReactNode } from "react"

type PopoverProps = {
    children: ReactNode
    content: ReactNode
    title?: string 
    description?: string 
    placement?: "bottom" | "bottom-start" | "bottom-end" | "top" | "top-start" | "top-end" | "left" | "left-start" | "left-end" | "right" | "right-start" | "right-end"
}

export function Popover({ children, content, title, description, placement }: PopoverProps) {
    return (
        <ArcPopover.Root
            positioning={{
                placement: placement ? placement : "bottom"
            }}
        >
            <ArcPopover.Trigger>{children}</ArcPopover.Trigger>
            <Portal>
                <ArcPopover.Positioner>
                    <ArcPopover.Content>
                        {title && (<ArcPopover.Title>{title}</ArcPopover.Title>) }
                        {description && (<ArcPopover.Description>{description}</ArcPopover.Description>)}
                        {content}
                    </ArcPopover.Content>
                </ArcPopover.Positioner>
            </Portal>
        </ArcPopover.Root>
    )
}