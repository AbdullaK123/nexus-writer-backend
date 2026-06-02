import { Search } from "lucide-react"
import { Kbd } from "../../../../common";
import styles from "./SceneSearchPaletteHeader.module.css"


type SceneSearchPaletteHeaderProps = {
    query: string;
    onQueryChange: (query: string) => void;
}


export function SceneSearchPaletteHeader({
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
                    type="text" 
                    value={query}
                    onChange={(e) => onQueryChange(e.target.value)}
                />
            </div>
            <Kbd>ESC</Kbd>
        </div>
    )
}