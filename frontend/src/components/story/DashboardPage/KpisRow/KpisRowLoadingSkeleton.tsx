import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import { CardLoadingSkeleton } from "../../CardLoadingSkeleton";
import styles from "./KpisRow.module.css";

export function KpisRowLoadingSkeleton() {
  return (
    <div className={styles['row-container']}>
      <div className={styles['space-between']}>
        <span className="system-badge system-badge__nobg">[YOUR PROGRESS]</span>
        <LoadingSkeleton className={Some("")} />
      </div>
      <div className={styles['kpis-container']}>
        <CardLoadingSkeleton />
        <CardLoadingSkeleton />
        <CardLoadingSkeleton />
        <CardLoadingSkeleton />
      </div>
    </div>
  );
}