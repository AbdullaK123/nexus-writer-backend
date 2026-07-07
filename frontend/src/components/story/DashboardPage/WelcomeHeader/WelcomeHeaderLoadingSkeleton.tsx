import { Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../common";
import styles from "./WelcomeHeader.module.css";

export function WelcomeHeaderLoadingSkeleton() {
  return (
    <div className={styles['header-container']}>
      <div className={styles['welcome-section-container']}>
        <LoadingSkeleton className={Some('')} />
        <LoadingSkeleton className={Some('')} />
      </div>
      <div className={styles['search-section-container']}>
        <LoadingSkeleton className={Some('')} />
        <LoadingSkeleton className={Some('')} />
      </div>
    </div>
  );
}