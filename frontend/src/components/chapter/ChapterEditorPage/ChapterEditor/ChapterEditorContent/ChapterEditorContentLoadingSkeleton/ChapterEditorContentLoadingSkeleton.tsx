import { None, Some } from "oxide.ts";
import { LoadingSkeleton } from "../../../../../common";
import contentStyles from "../ChapterEditorContent.module.css";
import styles from "./ChapterEditorContentLoadingSkeleton.module.css";

function ParagraphSkeleton() {
  return (
    <div className={styles.group}>
      <LoadingSkeleton className={Some(`${styles.line} ${styles['w-70']}`)} />
      <LoadingSkeleton className={None} />
      <LoadingSkeleton className={None} />
      <LoadingSkeleton className={None} />
    </div>
  );
}

export function ChapterEditorContentLoadingSkeleton() {
  return (
    <div className={contentStyles['editor-shell']}>
      <div className={styles.stack}>
        <div className={styles.group}>
          <LoadingSkeleton className={Some(`${styles.line} ${styles['w-60']}`)} />
        </div>
        <ParagraphSkeleton />
        <ParagraphSkeleton />
        <div className={styles.group}>
          <LoadingSkeleton className={Some(`${styles.line} ${styles['w-90']}`)} />
          <LoadingSkeleton className={None} />
          <LoadingSkeleton className={Some(styles['w-80'])} />
        </div>
      </div>
    </div>
  );
}