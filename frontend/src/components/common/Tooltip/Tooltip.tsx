import { Tooltip as ArcToolTip } from "@ark-ui/react/tooltip"
import { Portal } from "@ark-ui/react/portal"
import styles from "./Tooltip.module.css"

export type TooltipProps = {
    message: string
    children: React.ReactNode
}


export function Tooltip({ message, children }: TooltipProps) {
    return (
        <ArcToolTip.Root
            positioning={{
                placement: "right",
                offset: {
                    mainAxis: 32,
                    crossAxis: 16
                }
            }}
        >
            <ArcToolTip.Trigger  
                className={styles['trigger']}
                asChild
            >
                {children}
            </ArcToolTip.Trigger>
            <Portal>
                <ArcToolTip.Positioner>
                    <ArcToolTip.Content
                        className={styles['content']}
                    >
                        {message}
                    </ArcToolTip.Content>
                </ArcToolTip.Positioner>
            </Portal>
        </ArcToolTip.Root>
    )
}