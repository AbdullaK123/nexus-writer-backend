import type { ReactNode } from "react";
import styles from "./AppShell.module.css"
import { SideRail, type SideRailProps } from "./SideRail";

export type AppShellProps = {
    children: ReactNode
    sideRail: SideRailProps
}


export function AppShell({ children, sideRail  }: AppShellProps) {
    return (
        <div className={styles['app-container']}>
            <SideRail 
                {...sideRail}
            />
            {children}
        </div>
    )
}