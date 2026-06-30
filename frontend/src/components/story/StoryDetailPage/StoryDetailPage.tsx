import { StoryOverview } from "./StoryOverview/StoryOverview";
import { StoryHeader } from "./StoryHeader/StoryHeader";
import { ChapterList } from "./ChapterList/ChapterList";
import { BookPulse } from "./BookPulse/BookPulse";
import { useStoryDetailPage } from "./useStoryDetailPage";
import styles from "./StoryDetailPage.module.css"

export function StoryDetailPage() {
  const { storyHeader, storyOverview, bookPulse, chapterList } = useStoryDetailPage()
  return (
    <div className={styles['content-container']}>
      <StoryHeader {...storyHeader} />
      <StoryOverview {...storyOverview} />
      <div className={styles['list-and-pulse-container']}>
        <ChapterList {...chapterList} />
        <BookPulse {...bookPulse} />
      </div>
    </div>
  )
}