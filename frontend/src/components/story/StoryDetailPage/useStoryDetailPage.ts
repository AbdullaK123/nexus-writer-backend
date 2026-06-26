import { useState } from "react";
import { useStoryChapters } from "../../../data/queries";
import type { ChapterListProps } from "./ChapterList/ChapterList";
import type { StoryHeaderProps } from "./StoryHeader/StoryHeader";
import type { StoryOverviewProps } from "./StoryOverview/StoryOverview";
import { useNavigate, useSearch } from "@tanstack/react-router"
import { None, Option } from "oxide.ts";
import type { ApiError } from "../../../shared/types";
import type { AsyncState, ChapterListResponse } from "../../../infrastructure/api/types";


export type StoryDetailPageProps = {
    storyHeader: StoryHeaderProps,
    storyOverview: StoryOverviewProps,
    chapterList: ChapterListProps
}


export function useStoryDetailPage(): StoryDetailPageProps {

    const { storyId } = useSearch({ from: "/app/stories/$storyId" })

    const [storyChaptersState, refetchChapters] = useStoryChapters(storyId)

    const navigate = useNavigate()

    const [modalOpen, setModalOpen] = useState(false)

    const [selectedChapterId, setSelectedChapterId] = useState<Option<string>>(None)

    const getStoryHeaderProps = (state: AsyncState<ChapterListResponse, ApiError>) => {

        const common = {
            onNavigateToLibrary: () => navigate({ to: "/" }),
            onClickSettings: () => {},
            onAskNexus: () => {},
            onNewChapter: () => setModalOpen(true)
        }

        switch (state.status) {
            case "empty": 
                return {...common, storyTitle: None}
            case "error":
                return {...common, storyTitle: None}
            case "idle":
                return {...common, storyTitle: None}
            case "loading":
                return {...common, storyTitle: None}
            case "success":
                return {...common, storyTitle: state.data.unwrap().unwrap().storyTitle}
        }
    }

  

    return {
        storyHeader: {
            
        },
        storyOverview: {

        },
        chapterList: {

        }
    }

}