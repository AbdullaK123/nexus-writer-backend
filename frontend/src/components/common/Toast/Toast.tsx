import { Toast as ArcToast, Toaster, type ToastType } from "@ark-ui/react/toast"
import { Portal } from "@ark-ui/react/portal"
import { type ReactNode } from "react"
import { toaster } from "./toaster"
import styles from "./Toast.module.css"

type ToastProps = {
    children: ReactNode
}


const getAccentStyles = (type: ToastType | undefined) => {
    switch (type) {
        case "success": return styles['accent-left__success']
        case "error": return styles['accent-left__error']
        case "info": return styles['accent-left__info']
        case "loading": return styles['accent-left__info']
        case "warning": return styles['accent-left__warning']
        default: return styles['accent-left__info']
    }
}


export function Toast({ children }: ToastProps) {
    return (
        <>
            {children}
            <Portal>
                <Toaster toaster={toaster}>
                    {(toast) => (
                            <ArcToast.Root 
                                className={styles.Root} 
                                key={toast.id}
                            >
                                <div className="hstack">
                                    <div className={`${getAccentStyles(toast.type)}`}/>
                                    <div>
                                        <ArcToast.Title className={styles.Title}>{toast.title}</ArcToast.Title>
                                        <ArcToast.Description className={styles.Description}>{toast.description}</ArcToast.Description>
                                    </div>
                                </div>
                            </ArcToast.Root>
                    )}
                </Toaster>
            </Portal>
        </>
    )
}