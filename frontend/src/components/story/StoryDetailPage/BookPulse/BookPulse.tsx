import type { PulseDimension } from "../../../../infrastructure/api/types";
import { Button, EmptyState, ErrorState, LoadingSkeleton } from "../../../common";
import { None, Some } from "oxide.ts";
import styles from "./BookPulse.module.css"

export type BookPulseProps =
  | { status: 'loading' }
  | { status: 'error'; onRetry: () => void }
  | { status: 'empty' }
  | {
      status: 'ready'
      characters: PulseDimension
      plot: PulseDimension
      structure: PulseDimension
      world: PulseDimension
    }

export function BookPulse(props: BookPulseProps) {
  const getLabelStyles = (label: "healthy" | "needs-attention" | "watch" | "unavailable") => {
    switch (label) {
      case "healthy": return styles['text-healthy']
      case "needs-attention": return styles['text-warn']
      case "unavailable": return styles['text-not-available']
      case "watch": return styles['text-needs-attention']
    }
  }

  const getLabelText = (label: "healthy" | "needs-attention" | "watch" | "unavailable") => {
    switch (label) {
      case "healthy": return "healthy"
      case "needs-attention": return "needs attention"
      case "unavailable": return "not available"
      case "watch": return "watch"
    }
  }

  switch (props.status) {
    case 'loading':
      return (
        <div className={styles['content-container']}>
          <div className={styles['content-header']}>
            <div className={styles['system-tag-container']}>
              <span className="system-badge system-badge__nobg">[BOOK PULSE]</span>
              <p>Loading…</p>
            </div>
            <Button variant="ghost" onClick={() => {}}>→ FULL</Button>
          </div>
          <div className={styles['content']}>
            {[1,2,3,4].map((i) => (
              <div key={i} className={styles['pulse-card']}>
                <div className={styles['pulse-card-header']}>
                  <p className={styles['all-caps']}>&nbsp;</p>
                  <p>&nbsp;</p>
                </div>
                <LoadingSkeleton className={None} />
              </div>
            ))}
          </div>
        </div>
      )
    case 'error':
      return (
        <ErrorState
          headline="Error"
          title="Failed to load book pulse."
          description={None}
          action={Some(<Button variant="primary" onClick={props.onRetry}>Retry</Button>)}
        />
      )
    case 'empty':
      return (
        <EmptyState
          headline="No analytics yet"
          title="Pulse is not available yet"
          description={Some("Write a bit more and let the analytics agent run to see your book's pulse.")}
          action={None}
        />
      )
    case 'ready':
      return (
        <div className={styles['content-container']}>
          <div className={styles['content-header']}>
            <div className={styles['system-tag-container']}>
              <span className="system-badge system-badge__nobg">[BOOK PULSE]</span>
              <p>From the analytics agent</p>
            </div>
            <Button variant="ghost" onClick={() => {}}>→ FULL</Button>
          </div>
          <div className={styles['content']}>
            <div className={styles['pulse-card']}>
              <div className={styles['pulse-card-header']}>
                <p className={styles['all-caps']}>CHARACTERS</p>
                <p className={getLabelStyles(props.characters.label)}>
                  {getLabelText(props.characters.label)}
                </p>
              </div>
              <h3>{props.characters.headline}</h3>
              <p>{props.characters.report}</p>
            </div>
            <div className={styles['pulse-card']}>
              <div className={styles['pulse-card-header']}>
                <p className={styles['all-caps']}>PLOT</p>
                <p className={getLabelStyles(props.plot.label)}>
                  {getLabelText(props.plot.label)}
                </p>
              </div>
              <h3>{props.plot.headline}</h3>
              <p>{props.plot.report}</p>
            </div>
            <div className={styles['pulse-card']}>
              <div className={styles['pulse-card-header']}>
                <p className={styles['all-caps']}>STRUCTURE</p>
                <p className={getLabelStyles(props.structure.label)}>
                  {getLabelText(props.structure.label)}
                </p>
              </div>
              <h3>{props.structure.headline}</h3>
              <p>{props.structure.report}</p>
            </div>
            <div className={styles['pulse-card']}>
              <div className={styles['pulse-card-header']}>
                <p className={styles['all-caps']}>WORLD</p>
                <p className={getLabelStyles(props.world.label)}>
                  {getLabelText(props.world.label)}
                </p>
              </div>
              <h3>{props.world.headline}</h3>
              <p>{props.world.report}</p>
            </div>
          </div>
        </div>
      )
  }
}