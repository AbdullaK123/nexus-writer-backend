import { StoryOverview } from "./StoryOverview/StoryOverview";
import { StoryHeader } from "./StoryHeader/StoryHeader";
import { ChapterList } from "./ChapterList/ChapterList";
import { BookPulse } from "./BookPulse/BookPulse";
import { useStoryDetailPage } from "./useStoryDetailPage";

export function StoryDetailPage() {
  const { storyHeader, storyOverview, bookPulse, chapterList } = useStoryDetailPage()
  return (
    <div>
      <StoryHeader {...storyHeader} />
      <StoryOverview {...storyOverview} />
      <BookPulse {...bookPulse} />
      <ChapterList {...chapterList} />
    </div>
  )
}