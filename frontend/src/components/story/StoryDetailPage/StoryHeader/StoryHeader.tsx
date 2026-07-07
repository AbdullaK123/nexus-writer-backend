import { Button, ModalWithTrigger } from "../../../common";
import styles from "./StoryHeader.module.css"
import { None } from "oxide.ts"



export type StoryHeaderProps =
  | {
      status: 'loading'
      modalOpen: boolean
      onModalOpenChange: (open: boolean) => void
      chapterTitle: string
      onChapterTitleChange: (title: string) => void;
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: (title: string) => void
    } 
  | {
      status: 'error'
      message: string
      onRetry: () => void
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: () => void
    }
  | {
      status: 'empty'
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: () => void
    }
  | {
      status: 'ready'
      title: string
      modalOpen: boolean
      onModalOpenChange: (open: boolean) => void
      chapterTitle: string
      onChapterTitleChange: (title: string) => void
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: (title: string) => void
    } 

import { StoryHeaderLoadingSkeleton } from "./StoryHeaderLoadingSkeleton";

export function StoryHeader(props: StoryHeaderProps) {
  switch (props.status) {
    case 'loading':
      return <StoryHeaderLoadingSkeleton />
    case 'error':
      return (
        <div className={styles['header-container']}>
          <Button variant="ghost" onClick={props.onNavigateToLibrary}>{`← YOUR LIBRARY`}</Button>
          <div className={styles['btn-container']}>
            <p className={styles['red-text']}>X {props.message}</p>
            <Button variant="secondary" onClick={props.onRetry}>Retry</Button>
            <Button variant="secondary" onClick={props.onClickSettings}>Settings</Button>
            <Button variant="primary" onClick={props.onAskNexus}>Ask Nexus</Button>
            <Button variant="primary" onClick={props.onNewChapter}>+ New Chapter</Button>
          </div>
        </div>
      )
    case 'empty':
      return (
        <div className={styles['header-container']}>
          <Button variant="ghost" onClick={props.onNavigateToLibrary}>{`← YOUR LIBRARY`}</Button>
          <div className={styles['btn-container']}>
            <Button variant="secondary" onClick={props.onClickSettings}>Settings</Button>
            <Button variant="primary" onClick={props.onAskNexus}>Ask Nexus</Button>
            <Button variant="primary" onClick={props.onNewChapter}>+ New Chapter</Button>
          </div>
        </div>
      )
    case 'ready':
      return (
        <div className={styles['header-container']}>
          <Button variant="ghost" onClick={props.onNavigateToLibrary}>{`← YOUR LIBRARY / ${props.title.toUpperCase()}`}</Button>
          <div className={styles['btn-container']}>
            <Button variant="secondary" onClick={props.onClickSettings}>Settings</Button>
            <Button variant="primary" onClick={props.onAskNexus}>Ask Nexus</Button>
            <ModalWithTrigger
                open={props.modalOpen}
                onOpenChange={props.onModalOpenChange}
                closeTrigger={None}
                title={None}
                description={None}
                content={
                  <div className={styles['form-container']}>
                    <h2>Create a new chapter</h2>
                    <div className="hstack">
                      <input
                        type="text"
                        value={props.chapterTitle}
                        className="field__input"
                        placeholder="Give it a nice title..."
                        onChange={(e) => props.onChapterTitleChange(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') props.onNewChapter(props.chapterTitle)
                        }}
                      />
                      <Button variant="primary" onClick={() => props.onNewChapter(props.chapterTitle)}>
                        Submit
                      </Button>
                    </div>
                  </div>
                }
            >
              <Button variant="primary">+ New Chapter</Button>
            </ModalWithTrigger>
          </div>
        </div>
      )
  }
}