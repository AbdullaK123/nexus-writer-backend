import { Button, LoadingSkeleton, Nothing } from "../../../common";
import { ChapterSidebarItem, type ChapterSidebarItemProps } from "./ChapterSidebarItem";
import { PanelLeftOpen, PanelLeftClose } from 'lucide-react';
import styles from "./ChapterEditorSidebar.module.css"
import { Some } from "oxide.ts";

export type ChapterEditorSidebarProps = 
| { status: "error" }
| { status: "empty" }
| { status: "loading", open: boolean, onOpenChange: (e: boolean) => void }
| { status: "ready", open: boolean, storyTitle: string; items: ChapterSidebarItemProps[], onOpenChange: (e: boolean) => void}


export function ChapterEditorSidebar(props: ChapterEditorSidebarProps) {
    switch (props.status) {
        case "error":
        case "empty": {
            return <Nothing />
        }
        case "loading": {
            return (
                <aside className={`${styles['content']} ${props.open ? "": styles['closed']}`}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <LoadingSkeleton className={Some(styles['full-height'])} />
                        </div>
                        <Button
                            variant="ghost"
                            onClick={() => props.onOpenChange(props.open)}
                        >
                            {props.open ? (
                                <PanelLeftOpen 
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            ): (
                                <PanelLeftClose
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            )}
                        </Button>
                    </div>
                    <div className={styles['items-container']}>
                        <LoadingSkeleton className={Some(styles['full-height'])} />
                        <LoadingSkeleton className={Some(styles['full-height'])}/>
                        <LoadingSkeleton className={Some(styles['full-height'])}/>
                        <LoadingSkeleton className={Some(styles['full-height'])}/>
                    </div>
                </aside>
            )
        }
        case "ready":{
            return (
                <aside className={`${styles['content']} ${props.open ? "": styles['closed']}`}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <span className="system-badge system-badge__nobg">[Chapters]</span>
                            <h4>{props.storyTitle}</h4>
                        </div>
                        <span
                            className={styles['icon-btn']}
                            onClick={() => props.onOpenChange(props.open)}
                        >
                            {props.open ? (
                                <PanelLeftClose
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            ): (
                                <PanelLeftOpen
                                    color={"#ffffff"}
                                    width={24}
                                    height={24}
                                />
                            )}
                        </span>
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