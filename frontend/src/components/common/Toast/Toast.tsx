import { Toast as ArcToast, Toaster } from "@ark-ui/react/toast"
import { Portal } from "@ark-ui/react/portal"
import { type ReactNode } from "react"
import { toaster } from "./toaster"

type ToastProps = {
    children: ReactNode
}

export function Toast({ children }: ToastProps) {
    return (
        <>
            {children}
            <Portal>
                <Toaster toaster={toaster}>
                    {(toast) => (
                        <ArcToast.Root key={toast.id}>
                            <ArcToast.Title>{toast.title}</ArcToast.Title>
                            <ArcToast.Description>{toast.description}</ArcToast.Description>
                        </ArcToast.Root>
                    )}
                </Toaster>
            </Portal>
        </>
    )
}