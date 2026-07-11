import { Portal } from "@ark-ui/react";
import { Menu } from "@ark-ui/react/menu"
import { EllipsisVertical } from "lucide-react";
import styles from "./StoryCard.module.css"
import { useState } from "react"
import { Button, TriggerlessModal, useToast } from "../../../../common";
import { None, Some } from "oxide.ts";
import { useUpdateStory } from "../../../../../data/queries";
import type { StoryStatus } from "../../../../../infrastructure/api/types";



export function StoryCardMenu({ storyId }: { storyId: string }) {
    
    const [open, setOpen] = useState(false)
    const [modalOpen, setModalOpen] = useState(false)
    const [newTitle, setNewTitle] = useState("")
    const { success, error } = useToast()
    const { mutate: updateStory } = useUpdateStory(storyId);

    const onUpdateTitle = (title: string) =>
        updateStory({ title }, {
            onSuccess: () => {
                success("Success!", "Your story has a new title!")
            },
            onError: () => {
                error("Error", "Something went wrong and we couldn't update your story. The server might be experiencing issues.")
            },
            onSettled: () => {
                setNewTitle("")
                setModalOpen(false)
            }
        })

    const onUpdateStoryStatus = (status: StoryStatus) => 
        updateStory({ status }, {
            onSuccess: () => {
                success("Success!", `Your story is now ${status.toLowerCase()}`)
            },
            onError: () => {
                error("Error", "Something went wrong and we couldn't update your story's status. The server might be experiencing issues.")
            },
            onSettled: () => {
                setNewTitle("")
                setModalOpen(false)
            }
        })

    return (
        <>
            <Menu.Root
                lazyMount
                unmountOnExit
                open={open}
                onOpenChange={(e) => setOpen(e.open)}
                closeOnSelect
                composite={false}
                positioning={{ placement: "bottom-end", gutter: 8 }}
            >
                <Menu.Trigger asChild>
                    <button
                        type="button"
                        aria-label="Story actions"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <EllipsisVertical />
                    </button>
                </Menu.Trigger>

                <Portal>
                    <Menu.Positioner>
                        <Menu.Content className={styles['menu-container']}>
                            <Menu.Item
                                className={styles['menu-item']}
                                value="update-title"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setOpen(false)
                                    setModalOpen(true)
                                }}
                            >
                                Update Title
                            </Menu.Item>

                            <Menu.Root
                                lazyMount
                                unmountOnExit
                                composite={false}
                                positioning={{ placement: "right-start", gutter: 6 }}
                            >
                                <Menu.TriggerItem className={styles['menu-item']}>
                                    Update Status
                                </Menu.TriggerItem>
                                <Portal>
                                    <Menu.Positioner>
                                        <Menu.Content className={styles['menu-container']}>
                                            <Menu.Item 
                                                onClick={() => onUpdateStoryStatus("Ongoing")}
                                                className={styles['menu-item']} value="ongoing"
                                            >
                                                <span className="status-badge status-badge--ongoing" /> To Ongoing
                                            </Menu.Item>
                                            <Menu.Item 
                                                onClick={() => onUpdateStoryStatus("On Hiatus")}
                                                className={styles['menu-item']} value="hiatus"
                                            >
                                                <span className="status-badge status-badge--hiatus" /> To Hiatus
                                            </Menu.Item>
                                            <Menu.Item 
                                                onClick={() => onUpdateStoryStatus("Complete")}
                                                className={styles['menu-item']} value="complete"
                                            >
                                                <span className="status-badge status-badge--complete" /> To Complete
                                            </Menu.Item>
                                        </Menu.Content>
                                    </Menu.Positioner>
                                </Portal>
                            </Menu.Root>
                        </Menu.Content>
                    </Menu.Positioner>
                </Portal>
            </Menu.Root>

            <TriggerlessModal
                open={modalOpen}
                onOpenChange={setModalOpen}
                closeTrigger={None}
                title={Some("What do you want to rename it?")}
                description={None}
                initialFocusEl={None}
                finalFocusEl={None}
                content={
                    <div className={styles['form-container']}>
                        <div className="hstack">
                            <input
                                type="text"
                                value={newTitle}
                                className="field__input"
                                placeholder="Give it a nice new title..."
                                onChange={(e) => setNewTitle(e.target.value)}
                                onKeyDown={(e) => {
                                    if (e.key === "Enter") {
                                        onUpdateTitle(newTitle)
                                    }
                                }}
                            />
                            <Button
                                variant="primary"
                                onClick={() => onUpdateTitle(newTitle)}
                            >
                                Submit
                            </Button>
                        </div>
                    </div>
                }
            />
        </>
    )
}
