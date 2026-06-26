import { useState } from "react";
import { useStoryChapters } from "../../../data/queries";
import type { ChapterListProps } from "./ChapterList/ChapterList";
import type { StoryHeaderProps } from "./StoryHeader/StoryHeader";
import type { StoryOverviewProps } from "./StoryOverview/StoryOverview";
import { useSearch } from "@tanstack/react-router"
import { None, Option } from "oxide.ts";


export type StoryDetailPageProps = {
    storyHeader: StoryHeaderProps,
    storyOverview: StoryOverviewProps,
    chapterList: ChapterListProps
}


export function useStoryDetailPage() {

    const { storyId } = useSearch({ from: "/app/stories/$storyId" })

    const [storyChaptersState, refetchChapters] = useStoryChapters(storyId)

    const [modalOpen, setModalOpen] = useState(false)

    const [selectedChapterId, setSelectedChapterId] = useState<Option<string>>(None)
}