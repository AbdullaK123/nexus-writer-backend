import { useNavigate } from "@tanstack/react-router";
import styles from "./SideRail.module.css"
import { ModalWithTrigger } from "../../Modal";
import { useState } from "react";
import { None } from "oxide.ts";
import { useChatLinks, useEditorLinks } from "../../../../data/queries";
import { EditModalContent } from "./EditModalContent";
import { ChatModalContent } from "./ChatModalContent/ChatModalContent";


export function SideRail() {

    const navigate = useNavigate()
    const [editOpen, setEditOpen] = useState(false)
    const [chatOpen, setChatOpen] = useState(false)
    const [editLinksState, refetchEditLinks] = useEditorLinks()
    const [chatLinksState, refetchChatLinks] = useChatLinks()

    return (
        <nav className={styles['siderail-container']}>
            <span className={styles['siderail-item']}>NX</span>
            <button 
                className={styles['siderail-item']}
                onClick={() => navigate({ to: "/" })}
            >
                HOME
            </button>
            <ModalWithTrigger
                open={editOpen}
                onOpenChange={(e: boolean) => setEditOpen(e)}
                closeTrigger={None}
                title={None}
                description={None}
                content={
                    <EditModalContent 
                        state={editLinksState}
                        onRetry={refetchEditLinks}
                        onChange={(args) => {
                             navigate({
                                to: "/stories/$storyId/$chapterId",
                                params: {
                                    chapterId: args.chapterId,
                                    storyId: args.storyId
                                }
                            })
                            setEditOpen(false)
                        }}
                    />
                }
            >
                <button 
                    className={styles['siderail-item']}
                >
                    EDIT
                </button>
            </ModalWithTrigger>
            <ModalWithTrigger
                open={chatOpen}
                onOpenChange={(e: boolean) => setChatOpen(e)}
                closeTrigger={None}
                title={None}
                description={None}
                content={
                    <ChatModalContent 
                        state={chatLinksState}
                        onRetry={refetchChatLinks}
                        onChange={(storyId: string) => {
                            navigate({
                                to: "/stories/$storyId/chat/new",
                                params: {
                                    storyId: storyId
                                }
                            })
                            setChatOpen(false)
                        }}
                    />
                }
            >
                <button 
                    className={styles['siderail-item']}
                >
                    CHAT
                </button>
            </ModalWithTrigger>
            <button 
                className={styles['siderail-item']}
                onClick={() => navigate({ to: "/settings"})}
            >
                SET
            </button>
        </nav>
    )
}