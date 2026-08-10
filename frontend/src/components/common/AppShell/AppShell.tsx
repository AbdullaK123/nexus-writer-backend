import type { ReactNode } from "react";
import styles from "./AppShell.module.css"
import { SideRail } from "./SideRail";

export type AppShellProps = {
    children: ReactNode
}


export function AppShell({ children }: AppShellProps) {
    return (
        <div className={styles['app-container']}>
            <SideRail />
            {children}
        </div>
    )
}