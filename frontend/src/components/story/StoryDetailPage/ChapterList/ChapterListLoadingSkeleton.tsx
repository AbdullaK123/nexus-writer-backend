import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import styles from "./ChapterList.module.css";
import filterStyles from "./ChapterListFilterBar/ChapterListFilterBar.module.css";

export function ChapterListLoadingSkeleton() {
  return (
    <div className={styles['content']}>
      <div className={filterStyles['main-content']}>
        <div className={filterStyles['count-container']}>
          <LoadingSkeleton className={Some('system-badge')} />
          <LoadingSkeleton className={Some('')} />
        </div>
        <div className={filterStyles['filter-chip-container']}>
          <LoadingSkeleton className={Some('btn')} />
          <LoadingSkeleton className={Some('btn')} />
          <LoadingSkeleton className={Some('btn')} />
        </div>
      </div>
      <div className={styles['list-items']}>
        {Array.from({ length: 5 }).map((_, idx) => (
          <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: 'var(--space-4)' }} className="card">
            <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center', width: '60%' }}>
              <LoadingSkeleton className={Some('')} />
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)', width: '100%' }}>
                <LoadingSkeleton className={Some('')} />
                <LoadingSkeleton className={Some('')} />
              </div>
            </div>
            <LoadingSkeleton className={Some('')} />
          </div>
        ))}
      </div>
    </div>
  );
}
