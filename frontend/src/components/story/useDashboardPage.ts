import { useEffect, useEffectEvent, useState, type ChangeEvent } from "react";
import { useCreateStory, useDashboard, useStories } from "../../data/queries";
import { useToast } from "../common";
import { useRouteContext } from "@tanstack/react-router";


export function useDashboardPage() {

    const [modalOpen, setModalOpen] = useState(false)
    const [storyTitle, setStoryTitle] = useState("")

    const { error, success } = useToast()

    const {
        data: stories,
        isLoading: storiesLoading,
        isError: storiesError,
        refetch: refetchStories
    } = useStories()

    const {
        mutate: createStory,
        isError: createStoryError,
        isSuccess: createStorySuccess
    } = useCreateStory()

    const {
        data: dashboard,
        isLoading: dashboardLoading,
        isError: dashboardError,
        refetch: refetchDashboard
    } = useDashboard()

    const onStoryError = useEffectEvent(() => {
        error("Failed to load your stories.", "Something went wrong. If the problem persists, please contact support.")
    })

    const onDashboardError = useEffectEvent(() => {
        error("Failed to load you dashboard.", "Something went wrong. If the problem persits, please contact support.")
    })

    const onStoryCreateError = useEffectEvent(() => {
        error("Failed to create your story", "Something went wrong. If the problem persists, please contact support.")
    })

    const onStoryCreateSuccess = useEffectEvent(() => {
        success("Success!", "Your story has been successfully created! Happy Writing!")
    })

    useEffect(() => {
        if (storiesError) onStoryError()
    }, [storiesError])

     useEffect(() => {
        if (dashboardError) onDashboardError()
    }, [dashboardError])

    useEffect(() => {
        if (createStoryError) {
            onStoryCreateError()
        }
    }, [createStoryError])

    useEffect(() => {
        if (createStorySuccess) {
            onStoryCreateSuccess()
        }
    }, [createStorySuccess])

    const ctx = useRouteContext({ from: "/app" })

    return {
        welcomeHeader: {
            username: ctx.auth.user.unwrap().username,
            onEnterDown: (query: string) => console.log(query)
        },
        dashboard: {
            kpisRow: dashboard ? {
                totalWords: dashboard?.totalWords,
                storyCount: dashboard?.totalStories,
                totalChapters: dashboard?.chaptersTotal,
                chaptersPublished: dashboard?.chaptersPublished,
                currentStreak: dashboard?.streakDays,
                totalScenesTracked: dashboard?.scenesTracked
            } : undefined,
            jumpBackInRow: {
                chapterCards: dashboard ? dashboard.jumpBackIn.map(
                    (chapterCard) => ({...chapterCard, onClick: () => {}})
                ) : []
            },
            isLoading: dashboardLoading,
            isError: dashboardError,
            isEmpty: dashboard && dashboard.jumpBackIn.length === 0
        },
        stories: {
            libraryGrid: {
                stories: stories ? stories.stories.map(
                     (storyCard) => ({...storyCard, onClick: () => {}})
                 ) : [],
                 modalOpen: modalOpen,
                 storyTitle: storyTitle,
                 onStoryTitleChange: (e: ChangeEvent<HTMLInputElement>) => setStoryTitle(e.target.value),
                 onModalOpenChange: (e: boolean) => setModalOpen(e),
                 onNewStory: (title: string) => {
                    try {
                        createStory({title: title})
                    } finally {
                        setModalOpen(false)
                    }
                 }
            },
            isLoading: storiesLoading,
            isError: storiesError,
            isEmpty: stories && stories.stories.length === 0
        },
        refetch: {
            dashboard: refetchDashboard,
            stories: refetchStories
        }
    }
}