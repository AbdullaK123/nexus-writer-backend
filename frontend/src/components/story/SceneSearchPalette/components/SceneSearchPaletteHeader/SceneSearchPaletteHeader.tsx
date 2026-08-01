import { Search } from "lucide-react"
import { Kbd } from "../../../../common";
import styles from "./SceneSearchPaletteHeader.module.css"


export type SceneSearchPaletteHeaderProps = {
    modalInputId: string
    query: string;
    onQueryChange: (query: string) => void;
}


export function SceneSearchPaletteHeader({
    modalInputId,
    query,
    onQueryChange
}: SceneSearchPaletteHeaderProps) {
    return (
        <div className={styles['header-container']}>
            <div className={styles['icon-input']}>
                <Search 
                    size={24}  
                    color="#0ff"
                />
                <input
                    id={modalInputId}
                    type="text" 
                    className="field__input"
                    value={query}
                    onChange={(e) => onQueryChange(e.target.value)}
                    onFocus={(e) => {
                        requestAnimationFrame(() => {
                            e.target.setSelectionRange(e.target.value.length, e.target.value.length)
                        })
                    }}
                />
            </div>
            <Kbd>ESC</Kbd>
        </div>
    )
}