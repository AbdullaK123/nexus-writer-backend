import { Button, Kbd } from "../../../../common";
import styles from "./SceneSearchPaletteFooter.module.css"


type SceneSearchPaletteFooterProps = {
    query: string 
    onAskAgent: (query: string) => void;
}


export function SceneSearchPaletteFooter({
    query,
    onAskAgent
}: SceneSearchPaletteFooterProps) {
    return (
        <div className={styles['footer-container']}>
            <div className={styles['kbd-container']}>
                <div>   
                    <Kbd>
                        ↑ ↓
                    </Kbd>
                    <p>navigate</p>
                </div>
                <div>
                    <Kbd>
                        ↵
                    </Kbd>
                    <p>open</p>
                </div>
                <div>
                    <Kbd>
                        ⇧ ↵
                    </Kbd>
                    <p>open in new tab</p>
                </div>
            </div>
            <Button 
                onClick={() => onAskAgent(query)}
                variant="ghost"
            >
                Ask the agent →
            </Button>
        </div>
    )
}