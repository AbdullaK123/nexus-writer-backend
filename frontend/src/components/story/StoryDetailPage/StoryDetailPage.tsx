import { StoryOverview } from "./StoryOverview/StoryOverview";
import { StoryHeader } from "./StoryHeader/StoryHeader";
import { ChapterList } from "./ChapterList/ChapterList";
import { useStoryDetailPage } from "./useStoryDetailPage";

export function StoryDetailPage() {
  const { storyHeader, storyOverview, chapterList } = useStoryDetailPage()
  return (
    <div>
      <StoryHeader {...storyHeader} />
      <StoryOverview {...storyOverview} />
      <ChapterList {...chapterList} />
    </div>
  )
}