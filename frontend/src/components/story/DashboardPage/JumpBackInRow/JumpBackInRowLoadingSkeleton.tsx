import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import { CardLoadingSkeleton } from "../../CardLoadingSkeleton";
import styles from "./JumpBackInRow.module.css";

export function JumpBackInRowLoadingSkeleton() {
  return (
    <div className={styles['main-content']}>
      <div className={styles['header']}>
        <span className="system-badge system-badge__nobg">[JUMP BACK IN]</span>
        <LoadingSkeleton className={Some("")} />
      </div>
      <div className={styles['content']}>
        <CardLoadingSkeleton />
        <CardLoadingSkeleton />
        <CardLoadingSkeleton />
      </div>
    </div>
  );
}