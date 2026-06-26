import { Button, LoadingSkeleton } from "../../../common";
import styles from "./StoryHeader.module.css"
import { None } from "oxide.ts"

export type StoryHeaderProps =
  | {
      status: 'loading'
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: () => void
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
      onNavigateToLibrary: () => void
      onClickSettings: () => void
      onAskNexus: () => void
      onNewChapter: () => void
    }

export function StoryHeader(props: StoryHeaderProps) {
  switch (props.status) {
    case 'loading':
      return (
        <div className={styles['header-container']}>
          <LoadingSkeleton className={None} />
          <div className={styles['btn-container']}>
            <Button variant="secondary" onClick={props.onClickSettings}>Settings</Button>
            <Button variant="primary" onClick={props.onAskNexus}>Ask Nexus</Button>
            <Button variant="primary" onClick={props.onNewChapter}>+ New Chapter</Button>
          </div>
        </div>
      )
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
            <Button variant="primary" onClick={props.onNewChapter}>+ New Chapter</Button>
          </div>
        </div>
      )
  }
}