import { LoadingSkeleton, Nothing } from "../../../common";
import { ChapterSidebarItem, type ChapterSidebarItemProps } from "./ChapterSidebarItem";
import { PanelLeftOpen, PanelLeftClose } from 'lucide-react';
import styles from "./ChapterEditorSidebar.module.css"
import { Some } from "oxide.ts";
import { useNavigate } from "@tanstack/react-router"
import { DragDropProvider } from "@dnd-kit/react"
import { isSortable } from "@dnd-kit/react/sortable";

export type ChapterEditorSidebarProps = 
| { status: "empty" }
| { status: "loading"}
| { 
    status: "ready", 
    open: boolean, 
    storyId: string; 
    storyTitle: string; 
    items: ChapterSidebarItemProps[], 
    onReorder: (fromPos: number, toPos: number) => void
    onOpenChange: (e: boolean) => void
 }


export function ChapterEditorSidebar(props: ChapterEditorSidebarProps) {

    const navigate = useNavigate()

    switch (props.status) {
        case "empty": {
            return <Nothing />
        }
        case "loading": {
            return (
                <aside className={styles['content']}>
                    <div className={styles['header']}>
                        <div className={styles['header__label']}>
                            <LoadingSkeleton className={Some(styles['loading-pill'])} />
                        </div>
                    </div>
                    <div className={styles['items-container']}>
                        <LoadingSkeleton className={Some(styles['loading-pill'])} />
                        <LoadingSkeleton className={Some(styles['loading-pill'])}/>
                        <LoadingSkeleton className={Some(styles['loading-pill'])}/>
                        <LoadingSkeleton className={Some(styles['loading-pill'])}/>
                    </div>
                </aside>
            )
        }
        case "ready":{
            return (
                <aside className={`${styles['content']} ${props.open ? "": styles['closed']}`}>
                    <div className={styles['header']}>
                        <span id="badge" className="system-badge system-badge__nobg">[Chapters]</span>
                        <div className={styles['header__label']}>
                            <h4 
                                role="button"
                                id="back-btn"
                                className={styles['back-btn']}
                                onClick={() => navigate({ to: "/stories/$storyId", params: {storyId: props.storyId} }) }
                            >
                                ← {props.storyTitle}
                            </h4>
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
                    </div>
                    <DragDropProvider
                        onDragEnd={(event) => {

                            if (event.canceled) return
                            
                            const { source } = event.operation

                            if (!isSortable(source)) return

                            const fromPos = source.initialIndex
                            const toPos = source.index

                            props.onReorder(fromPos, toPos)       
                        }}
                    >
                         <div className={styles['items-container']}>
                            {props.items.map((item) => (
                                <ChapterSidebarItem
                                    key={item.chapterId}
                                    {...item}
                                />
                            ))}
                        </div>
                    </DragDropProvider>
                </aside>
            )
        }

    
    }
}