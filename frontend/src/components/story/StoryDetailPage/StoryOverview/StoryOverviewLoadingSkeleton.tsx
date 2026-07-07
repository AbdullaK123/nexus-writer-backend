import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import styles from "./StoryOverview.module.css";

export function StoryOverviewLoadingSkeleton() {
  return (
    <div className={styles['overview-container']}> 
      <div className={styles['details-container']}>
        <div className={styles['details-header']}>
          <LoadingSkeleton className={Some('system-badge')} />
          <LoadingSkeleton className={Some('')} />
        </div>
        <div className={styles['summary-container']}> 
          <LoadingSkeleton className={Some('')} />
          <LoadingSkeleton className={Some('')} />
        </div>
      </div>
      <div className={styles['stats-container']}>
        <LoadingSkeleton className={Some('')} />
        <LoadingSkeleton className={Some('')} />
        <LoadingSkeleton className={Some('')} />
        <LoadingSkeleton className={Some('')} />
      </div>
    </div>
  );
}
