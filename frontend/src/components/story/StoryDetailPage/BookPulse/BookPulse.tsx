import type { PulseDimension } from "../../../../infrastructure/api/types";
import { Button, EmptyState, LoadingSkeleton } from "../../../common";
import { None, Some, Option } from "oxide.ts";
import { useMemo, useState } from "react"
import styles from "./BookPulse.module.css"
import { FilterChipNoCounts } from "../../DashboardPage/LibraryGrid/FilterChip/FilterChip";

export type BookPulseProps =
  | { status: 'loading' }
  | { status: 'empty' }
  | {
      status: 'ready'
      onDigIntoThis: (pulse: PulseDimension) => void
      threadCreationPending: boolean
      characters: PulseDimension
      plot: PulseDimension
      structure: PulseDimension
      world: PulseDimension
    }

export function BookPulse(props: BookPulseProps) {
  const [selectedLense, setSelectedLense] = useState<"characters" | "plot" | "structure" | "world">("characters")

  const selectedDimension: Option<PulseDimension> = useMemo(() => {
    if (props.status !== "ready") return None
    switch (selectedLense) {
      case "characters": return Some(props.characters)
      case "plot": return Some(props.plot)
      case "structure": return Some(props.structure)
      case "world": return Some(props.world)
    }
  }, [props, selectedLense])

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

  const renderPulseCard = (
    lense: "characters" | "plot" | "structure" | "world", 
    dimension: PulseDimension,
    onDigIntoThis: (pulse: PulseDimension) => void,
    threadCreationPending: boolean
  ) => (
    <div className={styles['pulse-card']}>
      <div className={styles['pulse-card-header']}>
        <p className={styles['all-caps']}>{lense}</p>
        <p className={getLabelStyles(dimension.label)}>{getLabelText(dimension.label)}</p>
      </div>
      <h3>{dimension.headline}</h3>
      <div className={styles['pulse-section']}>
        <p className={styles['pulse-section-label']}>What's working</p>
        <p>{dimension.whats_working}</p>
      </div>
      <div className={styles['pulse-section']}>
        <p className={styles['pulse-section-label']}>What's not working</p>
        <p>{dimension.whats_not_working}</p>
        <Button
          variant="secondary"
          disabled={threadCreationPending}
          onClick={() => onDigIntoThis(dimension)}
        >
          {threadCreationPending ? "Opening investigation···" : "Dig into this →"}
        </Button>
      </div>
      {dimension.evidence_chapters.length > 0 && (
        <p className={styles['evidence-chapters']}>
          Evidence: Chapters {dimension.evidence_chapters.join(", ")}
        </p>
      )}
    </div>
  )

  switch (props.status) {
    case 'loading':
      return (
        <div className={styles['content-container']}>
          <div className={styles['content-header']}>
            <div className={styles['system-tag-container']}>
              <span className="system-badge system-badge__nobg">[BOOK PULSE]</span>
              <p>Loading…</p>
            </div>
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
    case 'empty':
      return (
        <EmptyState
          headline="No analytics yet"
          title="Pulse is not available yet"
          description={Some("Write a bit more and let the analytics agent run to see your book's pulse.")}
          action={None}
        />
      )
    case 'ready': {
      const unwrappedDimension = selectedDimension.unwrap()
      return (
        <div className={styles['content-container']}>
          <div className={styles['content-header']}>
            <div className={styles['system-tag-container']}>
              <span className="system-badge system-badge__nobg">[BOOK PULSE]</span>
              <p>From the analytics agent</p>
            </div>
          </div>
          <div className={styles['actions-container']}>
            <FilterChipNoCounts label="characters" onClick={() => setSelectedLense("characters")} status={selectedLense === "characters" ? "selected" : "idle"} />
            <FilterChipNoCounts label="plot" onClick={() => setSelectedLense("plot")} status={selectedLense === "plot" ? "selected" : "idle"} />
            <FilterChipNoCounts label="structure" onClick={() => setSelectedLense("structure")} status={selectedLense === "structure" ? "selected" : "idle"} />
            <FilterChipNoCounts label="world" onClick={() => setSelectedLense("world")} status={selectedLense === "world" ? "selected" : "idle"} />
          </div>
          <div className={styles['content']}>
            {renderPulseCard(selectedLense, unwrappedDimension, props.onDigIntoThis, props.threadCreationPending)}
          </div>
        </div>
      )
    }
  }
}
