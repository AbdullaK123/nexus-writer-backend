import { type ReactNode } from "react"
import { Tabs as ArcTabs } from "@ark-ui/react/tabs"

type TabsProps = {
    tabs: Record<string, ReactNode>
    defaultTab: string
}

export function Tabs({ tabs, defaultTab }: TabsProps) {
    return (
        <ArcTabs.Root defaultValue={defaultTab}>
            <ArcTabs.List>
                {Object.keys(tabs).map((tabName) => (
                    <ArcTabs.Trigger key={tabName} value={tabName}>
                        {tabName}
                    </ArcTabs.Trigger>
                ))}
            </ArcTabs.List>
            {Object.keys(tabs).map((tabName: string) => (
                <ArcTabs.Content key={tabName} value={tabName}>
                    {tabs[tabName]}
                </ArcTabs.Content>
            ))}
        </ArcTabs.Root>
    )
}