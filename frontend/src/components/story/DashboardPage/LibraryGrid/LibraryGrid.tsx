import { BeginNewStoryCard } from "./BeginNewStoryCard";
import { FilterChip } from "./FilterChip/FilterChip";
import { StoryCard, type StoryCardProps } from "./StoryCard/StoryCard";
import styles from './LibraryGrid.module.css'

import { Button, EmptyState, ErrorState, Modal } from "../../../common";
import { None, Some } from "oxide.ts";
import { LibraryLoadingSkeleton } from "../LibraryLoadingSkeleton";

export type LibraryGridProps =
  | { status: 'loading' }
  | { status: 'error'; onRetry: () => void }
  | {
      status: 'empty'
      modalOpen: boolean
      onModalOpenChange: (e: boolean) => void
      storyTitle: string
      onStoryTitleChange: (v: string) => void
      onNewStory: (title: string) => void
    }
  | {
      status: 'ready'
      stories: StoryCardProps[]
      selected: 'all' | 'ongoing' | 'hiatus' | 'complete'
      counts: { all: number; ongoing: number; hiatus: number; complete: number }
      onSelect: (label: 'all' | 'ongoing' | 'hiatus' | 'complete') => void
      modalOpen: boolean
      onModalOpenChange: (e: boolean) => void
      storyTitle: string
      onStoryTitleChange: (v: string) => void
      onNewStory: (title: string) => void
    }

export function LibraryGrid(props: LibraryGridProps) {
  switch (props.status) {
    case 'loading':
      return <LibraryLoadingSkeleton />
    case 'error':
      return (
        <ErrorState
          headline="Error"
          title="Failed to load your stories."
          description={Some("Sorry we couldn't load your stories. The server might be experiencing issues. Please try again.")}
          action={Some(
            <Button variant="primary" onClick={props.onRetry}>
              Try Again
            </Button>
          )}
        />
      )
    case 'empty':
      return (
        <EmptyState
          headline="No stories yet"
          title="Your shelf is empty"
          description={Some(
            "Start with one story. Even a working title. The agent will read what you write as you write it, and the analytics fill in by themselves."
          )}
          action={Some(
            <Modal
              open={props.modalOpen}
              onOpenChange={props.onModalOpenChange}
              closeTrigger={None}
              title={None}
              description={None}
              content={
                <div className={styles['vstack']}>
                  <h2>Create a new Story</h2>
                  <div className="hstack">
                    <input
                      type="text"
                      value={props.storyTitle}
                      className="field__input"
                      placeholder="Give it a nice title..."
                      onChange={(e) => props.onStoryTitleChange(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') props.onNewStory(props.storyTitle)
                      }}
                    />
                    <Button variant="primary" onClick={() => props.onNewStory(props.storyTitle)}>
                      Submit
                    </Button>
                  </div>
                </div>
              }
            >
              <Button variant="primary">Begin a new story →</Button>
            </Modal>
          )}
        />
      )
    case 'ready':
      return (
        <div className={styles['main-container']}>
          <div className={styles['header']}>
            <div className={styles['header__title']}>
              <span className="system-badge system-badge__nobg">{`[STORIES - ${props.stories.length}]`}</span>
              <h2>Your Library</h2>
            </div>
            <div className={styles['header__filters']}>
              <FilterChip
                status={props.selected === 'all' ? 'selected' : 'idle'}
                label="all"
                count={props.counts.all}
                onClick={() => props.onSelect('all')}
              />
              <FilterChip
                status={props.selected === 'ongoing' ? 'selected' : 'idle'}
                label="ongoing"
                count={props.counts.ongoing}
                onClick={() => props.onSelect('ongoing')}
              />
              <FilterChip
                status={props.selected === 'hiatus' ? 'selected' : 'idle'}
                label="hiatus"
                count={props.counts.hiatus}
                onClick={() => props.onSelect('hiatus')}
              />
              <FilterChip
                status={props.selected === 'complete' ? 'selected' : 'idle'}
                label="complete"
                count={props.counts.complete}
                onClick={() => props.onSelect('complete')}
              />
            </div>
          </div>
          <div className={styles['content']}>
            {props.stories.length > 0 &&
              props.stories.map((story, idx) => (
                <StoryCard key={idx} {...story} />
              ))}
            <BeginNewStoryCard
              storyTitle={props.storyTitle}
              onStoryTitleChange={props.onStoryTitleChange}
              modalOpen={props.modalOpen}
              onModalOpenChange={props.onModalOpenChange}
              onNewStory={props.onNewStory}
            />
          </div>
        </div>
      )
  }
}