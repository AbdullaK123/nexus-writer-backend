import { Popover as ArcPopover } from "@ark-ui/react/popover"
import { Portal } from "@ark-ui/react/portal"
import { type ReactNode } from "react"
import { Option } from "oxide.ts"

type PopoverProps = {
    children: ReactNode
    content: ReactNode
    title: Option<string>
    description: Option<string>
    placement: Option<"bottom" | "bottom-start" | "bottom-end" | "top" | "top-start" | "top-end" | "left" | "left-start" | "left-end" | "right" | "right-start" | "right-end">
}

export function Popover({ children, content, title, description, placement }: PopoverProps) {
    return (
        <ArcPopover.Root
            positioning={{
                placement: placement.isSome() ? placement.unwrap() : "bottom"
            }}
        >
            <ArcPopover.Trigger>{children}</ArcPopover.Trigger>
            <Portal>
                <ArcPopover.Positioner>
                    <ArcPopover.Content>
                        {title.isSome() && (<ArcPopover.Title>{title.unwrap()}</ArcPopover.Title>) }
                        {description.isSome() && (<ArcPopover.Description>{description.unwrap()}</ArcPopover.Description>)}
                        {content}
                    </ArcPopover.Content>
                </ArcPopover.Positioner>
            </Portal>
        </ArcPopover.Root>
    )
}