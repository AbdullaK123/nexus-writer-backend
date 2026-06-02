import type { ReactNode } from "react";
import { SceneSearchPaletteFooter, SceneSearchPaletteHeader, SceneSearchResultList, type SceneSearchResultItemProps } from "./components";
import { Modal } from "../../common";
import styles from "./SceneSearchPalette.module.css"


type SceneSearchPaletteProps = {
    children: ReactNode
    open: boolean
    query: string 
    results: SceneSearchResultItemProps[]
    isLoading: boolean
    onOpenChange: (open: boolean) => void
    onQueryChange: (query: string) => void
    onSelectResult: (result: SceneSearchResultItemProps) => void;
    onAskAgent: (query: string) => void;
}

type SceneSearchPaletteContentProps = Omit<SceneSearchPaletteProps, 'children' | 'open' | 'onOpenChange'>

const SceneSearchPaletteContent = ({
    query,
    results,
    isLoading,
    onQueryChange,
    onSelectResult,
    onAskAgent,
}: SceneSearchPaletteContentProps) => (
    <div className={styles['palette-container']}>
        <SceneSearchPaletteHeader 
            query={query}
            onQueryChange={onQueryChange}
        />
        <SceneSearchResultList 
            isLoading={isLoading}
            onSelectResult={onSelectResult}
            results={results}
        />
        <SceneSearchPaletteFooter 
            query={query}
            onAskAgent={onAskAgent}
        />
    </div>
)

export function SceneSearchPalette({
    children,
    open,
    query,
    results,
    isLoading,
    onOpenChange,
    onQueryChange,
    onSelectResult,
    onAskAgent
}: SceneSearchPaletteProps) {
    return (
        <Modal
            open={open}
            onOpenChange={onOpenChange}
            content={
                <SceneSearchPaletteContent 
                    query={query}
                    results={results}
                    isLoading={isLoading}
                    onQueryChange={onQueryChange}
                    onSelectResult={onSelectResult}
                    onAskAgent={onAskAgent}
                />
            }
        >
            {children}
        </Modal>
    )
}