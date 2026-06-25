import { Portal } from "@ark-ui/react/portal";
import { Dialog } from "@ark-ui/react/dialog"
import { type ReactNode} from "react"
import styles from "./Modal.module.css"
import { Option } from "oxide.ts"

type ModalProps = {
    open: boolean
    onOpenChange: (e: boolean) => void
    children: ReactNode
    content: ReactNode
    closeTrigger: Option<ReactNode>
    title: Option<string>
    description: Option<string>
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
                        {closeTrigger.isSome() && (<Dialog.CloseTrigger>{closeTrigger.unwrap()}</Dialog.CloseTrigger>)}
                        {title.isSome() && (<Dialog.Title>{title.unwrap()}</Dialog.Title>)}
                        {description.isSome() && (
                            <Dialog.Description>
                                {description.unwrap()}
                            </Dialog.Description>
                        )}
                        {content}
                    </Dialog.Content>
                </Dialog.Positioner>
            </Portal>
        </Dialog.Root>
    )
}