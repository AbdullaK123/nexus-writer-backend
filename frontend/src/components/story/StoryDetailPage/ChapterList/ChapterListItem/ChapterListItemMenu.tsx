import { Portal } from "@ark-ui/react";
import { Menu } from "@ark-ui/react/menu"
import { EllipsisVertical } from "lucide-react";
import styles from "./ChapterListItem.module.css"
import { useState } from "react"
import { Button, TriggerlessModal, useToast } from "../../../../common";
import { None, Some } from "oxide.ts";
import { useDeleteChapter, useUpdateChapter } from "../../../../../data/queries";

export type ChapterListItemMenuProps = {
    storyId: string
    chapterId: string
    chapterStatus: "draft" | "published"
}

export function ChapterListItemMenu({ storyId, chapterId, chapterStatus }: ChapterListItemMenuProps) {
    
    const [open, setOpen] = useState(false)
    const [modalOpen, setModalOpen] = useState(false)
    const [confirmationModalOpen, setConfirmationModalOpen] = useState(false)
    const [newTitle, setNewTitle] = useState("")
    const { success, error } = useToast()
    const { mutate: updateChapter } = useUpdateChapter(chapterId)
    const { mutate: deleteChapter } = useDeleteChapter(chapterId, storyId)

    const onUpdateChapterTitle = (title: string) =>
        updateChapter({ title }, {
            onSuccess: () => {
                success("Success!", "Your chapter has a new title!")
            },
            onError: () => {
                error("Error", "Something went wrong and we couldn't update your chapter. The server might be experiencing issues.")
            },
            onSettled: () => {
                setNewTitle("")
                setModalOpen(false)
            }
        })

    const onUpdateChapterStatus = (published: boolean) => 
        updateChapter({ published }, {
            onSuccess: () => {
                success("Success!", `Your chapter is now ${published ? "published": "a draft"}`)
            },
            onError: () => {
                error("Error", "Something went wrong and we couldn't update your chapter. The server might be experiencing issues.")
            },
            onSettled: () => {
                setNewTitle("")
                setModalOpen(false)
            }
        })

    const onDeleteChapter = () => 
        deleteChapter(void {
            onSuccess: () => {
                success("Success!", "Your chapter has been deleted.")
            },
            onError: () => {
                error("Error", "Something went wrong and we couldn't delete your chapter. The server might be experiencing issues.")
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
                            {(chapterStatus === "published") ? (
                                <Menu.Item
                                    className={styles['menu-item']}
                                    value="unpublish-chapter"
                                    onClick={() => onUpdateChapterStatus(false)}
                                >
                                    Unpublish
                                </Menu.Item>
                            ): (
                                <Menu.Item
                                    className={styles['menu-item']}
                                    value="publish-chapter"
                                    onClick={() => onUpdateChapterStatus(true)}
                                >
                                    Publish
                                </Menu.Item>
                            )}
                            <Menu.Item
                                className={styles['menu-item']}
                                value="unpublish-chapter"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    setOpen(false)
                                    setConfirmationModalOpen(true)
                                }}
                            >
                                Delete
                            </Menu.Item>
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
                                        onUpdateChapterTitle(newTitle)
                                    }
                                }}
                            />
                            <Button
                                variant="primary"
                                onClick={() => onUpdateChapterTitle(newTitle)}
                            >
                                Submit
                            </Button>
                        </div>
                    </div>
                }
            />
             <TriggerlessModal
                open={confirmationModalOpen}
                onOpenChange={setConfirmationModalOpen}
                closeTrigger={None}
                title={Some("Are you sure? This can not be reversed")}
                description={None}
                initialFocusEl={None}
                finalFocusEl={None}
                content={
                    <div className={styles['form-container']}>
                        <div className="hstack">
                            <Button
                                variant="secondary"
                                onClick={() => setConfirmationModalOpen(false)}
                            >
                                Cancel
                            </Button>
                            <Button
                                variant="danger"
                                onClick={() => onDeleteChapter()}
                            >
                                Yes I'm sure
                            </Button>
                        </div>
                    </div>
                }
            />
        </>
    )
}
