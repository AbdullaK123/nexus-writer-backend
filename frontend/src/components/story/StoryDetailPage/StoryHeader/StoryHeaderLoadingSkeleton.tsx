import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import styles from "./StoryHeader.module.css";

export function StoryHeaderLoadingSkeleton() {
  return (
    <div className={styles['header-container']}>
      <LoadingSkeleton className={Some('btn btn--ghost')} />
      <div className={styles['btn-container']}>
        <LoadingSkeleton className={Some('btn btn--secondary')} />
        <LoadingSkeleton className={Some('btn btn--primary')} />
        <LoadingSkeleton className={Some('btn btn--primary')} />
      </div>
    </div>
  );
}
