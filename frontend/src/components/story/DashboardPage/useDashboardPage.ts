import { useEffect, useEffectEvent, useState, type ChangeEvent } from "react";
import { useCreateStory, useDashboard, useStories } from "../../../data/queries";
import { useToast } from "../../common";
import { useRouteContext } from "@tanstack/react-router";
import type { WelcomeHeaderProps } from "./WelcomeHeader";
import type { KpisRowProps } from "./KpisRow";
import type { JumpBackInRowProps } from "./JumpBackInRow";
import type { LibraryGridProps } from "./LibraryGrid/LibraryGrid";
import type { AsyncState, DashboardResponse, StoryGridResponse } from "../../../infrastructure/api/types";
import type { QueryObserverResult, RefetchOptions } from "@tanstack/react-query";
import type { ApiError } from "../../../shared/types";
import { None, Option, Some } from "oxide.ts"

export type DashboardProps = {
    kpisRow: Option<KpisRowProps>
    jumpBackInRow: JumpBackInRowProps,
    isLoading: boolean,
    isError: boolean,
    isEmpty: boolean
}

export type StoriesProps = {
    libraryGrid: LibraryGridProps
    storyTitle: string,
    onStoryTitleChange: (e: ChangeEvent<HTMLInputElement>) => void;
    isLoading: boolean,
    isError: boolean,
    isEmpty: boolean
}

export type RefetchProps = {
    dashboard: (options?: RefetchOptions) => Promise<QueryObserverResult<DashboardResponse, ApiError>>
    stories: (options?: RefetchOptions) => Promise<QueryObserverResult<StoryGridResponse, ApiError>>
}

export type DashboardPageProps = {
    welcomeHeader: WelcomeHeaderProps,
    dashboard: DashboardProps,
    stories: StoriesProps,
    refetch: RefetchProps
}

export function useDashboardPage(): DashboardPageProps {
    const [modalOpen, setModalOpen] = useState(false);
    const [storyTitle, setStoryTitle] = useState("");

    const { error, success } = useToast();
    const [storiesState, refetchStories] = useStories();
    const [dashboardState, refetchDashboard] = useDashboard();
    
    const { mutate: createStory } = useCreateStory();

    const onStoryError = useEffectEvent(() => {
        error("Failed to load your stories.", "Something went wrong. If the problem persists, please contact support.");
    });

    const onDashboardError = useEffectEvent(() => {
        error("Failed to load your dashboard.", "Something went wrong. If the problem persists, please contact support.");
    });

    useEffect(() => {
        if (storiesState.status === "error") onStoryError();
    }, [storiesState]);

    useEffect(() => {
        if (dashboardState.status === "error") onDashboardError();
    }, [dashboardState.status]);

    const ctx = useRouteContext({ from: "/app" });

    // 1. COMPILER FIX: Unwrapping happens safely inside the success block
    const getStoriesProps = (state: AsyncState<StoryGridResponse, ApiError>): StoriesProps => {
        const common = {
            modalOpen: modalOpen,
            onModalOpenChange: (e: boolean) => setModalOpen(e),
            onNewStory: (title: string) => {
                createStory({ title }, {
                    onSuccess: () => {
                        success("Success!", "Your story has been successfully created! Happy writing!");
                        setStoryTitle("");
                        setModalOpen(false);
                    },
                    onError: () => {
                        error("Failed to create your story.", "Something went wrong. If the problem persists, please contact support.");
                        setModalOpen(false);
                    }
                });
            }
        };

        const storyTitleProps = {
            storyTitle: storyTitle,
            onStoryTitleChange: (e: ChangeEvent<HTMLInputElement>) => setStoryTitle(e.target.value)
        }

        if (state.status === "idle" || state.status === "loading") {
            return {
                libraryGrid: { ...common, stories: [] },
                ...storyTitleProps,
                isLoading: true,
                isError: false,
                isEmpty: false,
            }
        }
                
        if (state.status === "empty") {
            return {
                libraryGrid: { ...common, stories: [] },
                ...storyTitleProps,
                isLoading: false,
                isError: false,
                isEmpty: true,
            };
        }
                
        if (state.status === "error") {
            return {
                libraryGrid: { ...common, stories: [] },
                ...storyTitleProps,
                isLoading: false,
                isError: true,
                isEmpty: false,
            };
        }
             
        const rawData = state.data.unwrap().unwrap();

        const mappedStories = rawData.stories.map((story) => ({
            ...story,
            onClick: () => {}
        }));

        return {
            libraryGrid: { ...common, stories: mappedStories },
            ...storyTitleProps,
            isLoading: false,
            isError: false,
            isEmpty: mappedStories.length === 0,
        };
    
                // Safely unwrap data here since status === "success" guarantees Option holds Ok varian
    };

    // 2. Separate formatting for the dashboard state
    const getDashboardProps = (state: AsyncState<DashboardResponse, ApiError>): DashboardProps => {
        const isLoading = state.status === "loading" || state.status === "idle";
        const isError = state.status === "error";
        const isEmpty = state.status === "empty";

        if (state.status !== "success") {
            return {
                kpisRow: None,
                jumpBackInRow: { chapterCards: [] },
                isLoading,
                isError,
                isEmpty
            };
        }

        const data = state.data.unwrap().unwrap();
        return {
            kpisRow: Some({
                totalWords: data.totalWords,
                storyCount: data.totalStories,
                totalChapters: data.chaptersTotal,
                chaptersPublished: data.chaptersPublished,
                currentStreak: data.streakDays,
                totalScenesTracked: data.scenesTracked
            }),
            jumpBackInRow: {
                chapterCards: data.jumpBackIn.map((chapterCard) => ({ ...chapterCard, onClick: () => {} }))
            },
            isLoading: false,
            isError: false,
            isEmpty: data.jumpBackIn.length === 0
        };
    };

    // 3. Consume the formatting blocks directly into your execution payload
    return {
        welcomeHeader: {
            username: ctx.auth.user.unwrap().username,
            profileImageUrl: ctx.auth.user.unwrap().profileImg,
            onEnterDown: (query: string) => console.log(query)
        },
        dashboard: getDashboardProps(dashboardState),
        stories: getStoriesProps(storiesState),
        refetch: {
            dashboard: refetchDashboard,
            stories: refetchStories
        }
    };
}
