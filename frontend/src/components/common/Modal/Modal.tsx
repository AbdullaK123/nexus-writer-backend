import { Portal } from "@ark-ui/react/portal";
import { Dialog } from "@ark-ui/react/dialog"
import { type ReactNode } from "react"


type ModalProps = {
    children: ReactNode
    content: ReactNode
    closeTrigger: ReactNode
    title: string
    description?: string
}

export function Modal({ children, content, closeTrigger, title, description }: ModalProps) {
    return (
        <Dialog.Root>
            <Dialog.Trigger>{children}</Dialog.Trigger>
            <Portal>
                <Dialog.Backdrop />
                <Dialog.Positioner>
                    <Dialog.Content>
                        <Dialog.CloseTrigger>{closeTrigger}</Dialog.CloseTrigger>
                        <Dialog.Title>{title}</Dialog.Title>
                        {description && (
                            <Dialog.Description>
                                {description}
                            </Dialog.Description>
                        )}
                        {content}
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    )
}