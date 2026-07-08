import { Portal } from "@ark-ui/react/portal"
import { Dialog } from "@ark-ui/react/dialog"
import { type ReactNode, type ReactElement } from "react"
import styles from "./Modal.module.css"
import { Option } from "oxide.ts"

export type FocusGetter = () => HTMLElement | null

function optionToUndefined<T>(option: Option<T>): T | undefined {
    return option.isSome() ? option.unwrap() : undefined
}

export type ModalWithTriggerProps = {
    open: boolean
    onOpenChange: (open: boolean) => void
    children: ReactElement
    content: ReactNode
    closeTrigger: Option<ReactElement>
    title: Option<string>
    description: Option<string>
}

export type TriggerlessModalProps = {
    open: boolean
    onOpenChange: (open: boolean) => void
    content: ReactNode
    closeTrigger: Option<ReactElement>
    title: Option<string>
    description: Option<string>
    initialFocusEl: Option<FocusGetter>
    finalFocusEl: Option<FocusGetter>
}

export function ModalWithTrigger({
    open,
    onOpenChange,
    children,
    content,
    closeTrigger,
    title,
    description,
}: ModalWithTriggerProps) {
    return (
        <Dialog.Root open={open} onOpenChange={(e) => onOpenChange(e.open)}>
            <Dialog.Trigger asChild>
                {children}
            </Dialog.Trigger>

            <Portal>
                <Dialog.Backdrop className={styles["modal__backdrop"]} />
                <Dialog.Positioner className={styles["modal__positioner"]}>
                    <Dialog.Content className={styles["modal__content"]}>
                        {closeTrigger.isSome() && (
                            <Dialog.CloseTrigger asChild>
                                {closeTrigger.unwrap()}
                            </Dialog.CloseTrigger>
                        )}

                        {title.isSome() && (
                            <Dialog.Title className={styles['modal__title']}>{title.unwrap()}</Dialog.Title>
                        )}

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

export function TriggerlessModal({
    open,
    onOpenChange,
    content,
    closeTrigger,
    title,
    description,
    initialFocusEl,
    finalFocusEl,
}: TriggerlessModalProps) {
    return (
        <Dialog.Root
            open={open}
            onOpenChange={(e) => onOpenChange(e.open)}
            initialFocusEl={optionToUndefined(initialFocusEl)}
            finalFocusEl={optionToUndefined(finalFocusEl)}
        >
            <Portal>
                <Dialog.Backdrop className={styles["modal__backdrop"]} />
                <Dialog.Positioner className={styles["modal__positioner"]}>
                    <Dialog.Content className={styles["modal__content"]}>
                        {closeTrigger.isSome() && (
                            <Dialog.CloseTrigger asChild>
                                {closeTrigger.unwrap()}
                            </Dialog.CloseTrigger>
                        )}

                        {title.isSome() && (
                            <Dialog.Title>{title.unwrap()}</Dialog.Title>
                        )}

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