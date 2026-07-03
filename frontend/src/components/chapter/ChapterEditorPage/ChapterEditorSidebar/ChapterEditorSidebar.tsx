import { Button } from "../../../common";
import { ChapterSidebarItem, type ChapterSidebarItemProps } from "./ChapterSidebarItem";
import { PanelLeftOpen, PanelLeftClose } from 'lucide-react';
import styles from "./ChapterEditorSidebar.module.css"

export type ChapterEditorSidebarProps = 
| { status: "open", storyTitle: string; items: ChapterSidebarItemProps[], onClose: () => void }
| { status: "closed", storyTitle: string; items: ChapterSidebarItemProps[], onOpen: () => void}


export function ChapterEditorSidebar(props: ChapterEditorSidebarProps) {
    switch (props.status) {
        case "open": {
            return (
                <aside className={styles['content']}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <span className="system-badge system-badge__nobg">[Chapters]</span>
                            <h4>{props.storyTitle}</h4>
                        </div>
                        <Button
                            variant="ghost"
                            onClick={props.onClose}
                        >
                            <PanelLeftOpen 
                                color={"#ffffff"}
                                width={48}
                                height={48}
                            />
                        </Button>
                    </div>
                    <div className={styles['items-container']}>
                        {props.items.map((item, idx) => (
                            <ChapterSidebarItem
                                key={idx}
                                {...item}
                             />
                        ))}
                    </div>
                </aside>
            )
        }
        case "closed":{
            return (
                <aside className={`${styles['content']} ${styles['closed']}`}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <span className="system-badge system-badge__nobg">[Chapters]</span>
                            <h4>{props.storyTitle}</h4>
                        </div>
                        <Button
                            variant="ghost"
                            onClick={props.onOpen}
                        >
                            <PanelLeftClose 
                                color={"#ffffff"}
                                width={48}
                                height={48}
                            />
                        </Button>
                    </div>
                    <div className={styles['items-container']}>
                        {props.items.map((item, idx) => (
                            <ChapterSidebarItem
                                key={idx}
                                {...item}
                             />
                        ))}
                    </div>
                </aside>
            )
        }

    
    }
}