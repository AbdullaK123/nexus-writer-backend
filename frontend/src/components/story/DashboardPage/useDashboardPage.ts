import { useEffect, useEffectEvent, useState } from "react";
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

export type RefetchProps = {
    dashboard: (options?: RefetchOptions) => Promise<QueryObserverResult<DashboardResponse, ApiError>>
    stories: (options?: RefetchOptions) => Promise<QueryObserverResult<StoryGridResponse, ApiError>>
}

export type DashboardPageProps = {
    welcomeHeader: WelcomeHeaderProps,
    kpisRow: KpisRowProps,
    jumpBackInRow: JumpBackInRowProps,
    libraryGrid: LibraryGridProps,
    refetch: RefetchProps
}

export function useDashboardPage(): DashboardPageProps {
    // Local UI state scoped to LibraryGrid feature
    const [modalOpen, setModalOpen] = useState(false);
    const [storyTitle, setStoryTitle] = useState("");
    const [libraryFilter, setLibraryFilter] = useState<'all' | 'ongoing' | 'hiatus' | 'complete'>("all");
    // Local UI state scoped to WelcomeHeader feature
    const [searchQuery, setSearchQuery] = useState("");

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
    }, [storiesState.status]);

    useEffect(() => {
        if (dashboardState.status === "error") onDashboardError();
    }, [dashboardState.status]);

    const ctx = useRouteContext({ from: "/app" });

    // ---- Derive LibraryGrid DU from stories state ----
    const buildReadyLibraryGrid = (stories: { storyId: string; status: any; chapterNumber: number; title: string; wordCount: number; updatedAt: Date; onClick: (id: string) => void; }[]): LibraryGridProps => {
        const counts = stories.reduce(
            (acc, s) => {
                acc.all += 1;
                switch (s.status) {
                    case 'Ongoing': acc.ongoing += 1; break;
                    case 'On Hiatus': acc.hiatus += 1; break;
                    case 'Complete': acc.complete += 1; break;
                }
                return acc;
            },
            { all: 0, ongoing: 0, hiatus: 0, complete: 0 }
        );
        const filterFn = (s: typeof stories[number]) =>
            libraryFilter === 'all' ? true :
            libraryFilter === 'ongoing' ? s.status === 'Ongoing' :
            libraryFilter === 'hiatus' ? s.status === 'On Hiatus' :
            s.status === 'Complete';
        const filtered = stories.filter(filterFn);
        return {
            status: 'ready',
            stories: filtered,
            selected: libraryFilter,
            counts,
            onSelect: setLibraryFilter,
            modalOpen,
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
        } as const;
    };

    const libraryGrid: LibraryGridProps = ((): LibraryGridProps => {
        switch (storiesState.status) {
            case 'idle':
            case 'loading':
                return { status: 'loading' };
            case 'error':
                return { status: 'error', onRetry: () => { void refetchStories(); } };
            case 'empty':
                return {
                    status: 'empty',
                    modalOpen,
                    onModalOpenChange: (e: boolean) => setModalOpen(e),
                    storyTitle,
                    onStoryTitleChange: (v: string) => setStoryTitle(v),
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
            case 'success': {
                const rawData = storiesState.data.unwrap().unwrap();
                const mappedStories = rawData.stories.map((story) => ({
                    ...story,
                    onClick: () => {}
                }));
                // If success but no stories, surface 'empty' DU to show creation flow
                if (mappedStories.length === 0) {
                    return {
                        status: 'empty',
                        modalOpen,
                        onModalOpenChange: (e: boolean) => setModalOpen(e),
                        storyTitle,
                        onStoryTitleChange: (v: string) => setStoryTitle(v),
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
                }
                return buildReadyLibraryGrid(mappedStories);
            }
        }
    })();

    // ---- Derive KPIs DU and JumpBackIn DU from dashboard state ----
    const kpisRow: KpisRowProps = ((): KpisRowProps => {
        switch (dashboardState.status) {
            case 'idle':
            case 'loading':
                return { status: 'loading' };
            case 'error':
                return { status: 'error', onRetry: () => { void refetchDashboard(); } };
            case 'empty':
                return { status: 'empty' };
            case 'success': {
                const d = dashboardState.data.unwrap().unwrap();
                return {
                    status: 'ready',
                    totalWords: d.totalWords,
                    storyCount: d.totalStories,
                    totalChapters: d.chaptersTotal,
                    chaptersPublished: d.chaptersPublished,
                    currentStreak: d.streakDays,
                    totalScenesTracked: d.scenesTracked
                };
            }
        }
    })();

    const jumpBackInRow: JumpBackInRowProps = ((): JumpBackInRowProps => {
        switch (dashboardState.status) {
            case 'idle':
            case 'loading':
                return { status: 'loading' };
            case 'error':
                return { status: 'error', onRetry: () => { void refetchDashboard(); } };
            case 'empty':
                return { status: 'empty' };
            case 'success': {
                const d = dashboardState.data.unwrap().unwrap();
                if (d.jumpBackIn.length === 0) return { status: 'empty' };
                return {
                    status: 'ready',
                    chapterCards: d.jumpBackIn.map((chapterCard) => ({ ...chapterCard, onClick: () => {} }))
                };
            }
        }
    })();

    // 3. Compose final page payload of fully-resolved DUs
    return {
        welcomeHeader: {
            status: 'ready',
            username: ctx.auth.user.unwrap().username,
            profileImageUrl: ctx.auth.user.unwrap().profileImg,
            query: searchQuery,
            onQueryChange: setSearchQuery,
            onEnterDown: (query: string) => console.log(query)
        },
        kpisRow,
        jumpBackInRow,
        libraryGrid,
        refetch: {
            dashboard: refetchDashboard,
            stories: refetchStories
        }
    };
}
