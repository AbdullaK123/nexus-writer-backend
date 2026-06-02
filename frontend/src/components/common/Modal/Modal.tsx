import { Portal } from "@ark-ui/react/portal";
import { Dialog } from "@ark-ui/react/dialog"
import { type ReactNode} from "react"
import styles from "./Modal.module.css"

type ModalProps = {
    open: boolean
    onOpenChange: (e: boolean) => void
    children: ReactNode
    content: ReactNode
    closeTrigger?: ReactNode
    title?: string
    description?: string
}

export function Modal({ 
    open,
    onOpenChange,
    children, 
    content, 
    closeTrigger,
    title, 
    description
 }: ModalProps) {
    return (
        <Dialog.Root open={open} onOpenChange={(e) => onOpenChange(e.open)}>
            <Dialog.Trigger>{children}</Dialog.Trigger>
            <Portal>
                <Dialog.Backdrop className={styles['modal__backdrop']} />
                <Dialog.Positioner className={styles['modal__positioner']}>
                    <Dialog.Content className={styles['modal__content']}>
                        {closeTrigger && (<Dialog.CloseTrigger>{closeTrigger}</Dialog.CloseTrigger>)}
                        {title && (<Dialog.Title>{title}</Dialog.Title>)}
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